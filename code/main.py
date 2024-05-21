# import sendgrid  # using SendGrid's Python Library - https://github.com/sendgrid/sendgrid-python
from requests import get,post
import json
from datetime import datetime, timedelta
import os

def billing(event_data,context):
  user = os.getenv('USER')
  days_delta = int(os.getenv('DAYS_DELTA'))+1
  budget_amount = int(os.getenv('BUDGET'))
  DD_API_KEY = os.getenv('DD_API_KEY')
  DD_APPLICATION_KEY = os.getenv('DD_APPLICATION_KEY')
  slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
  # SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
  # from_email = os.getenv('FROM_EMAIL')
  # to_email = os.getenv('TO_EMAIL')

  print (f"Input received: days={days_delta}, budget={budget_amount}")
  payload={}
  headers = {
    'Accept': 'application/json',
    'DD-API-KEY': DD_API_KEY,
    'DD-APPLICATION-KEY': DD_APPLICATION_KEY
  }

  actual_cost = 0
  date = (datetime.today() - timedelta(days=days_delta)).strftime('%Y-%m-%d')
  url = f"https://api.datadoghq.com/api/v2/usage/estimated_cost?view=summary&start_date={date}"

  print(f"requesting bill for {date}...")
  response = get(url, headers=headers, data=payload, timeout=15)
  print("response received, processing...")
  print(response.status_code)

  r = json.loads(response.text)
  print(r)

  #Sorting Data for Proper Readability
  for datapoint in r['data'] :
    attr = datapoint['attributes']
    attr['charges'] = sorted(attr['charges'], key=lambda x: x['product_name'])
    attr['charges'] = sorted(attr['charges'], key=lambda x: x['charge_type'])

  for datapoint in r['data'] :
    attr = datapoint['attributes']
    components = '\n'.join(['\t '+item['product_name']+' ('+item['charge_type']+'): $'+str(item['cost']) for item in attr['charges'] if item['cost']>0])
    actual_cost = attr['total_cost']

    msg_date = f"Date: {attr['date'][:10]}\n"
    msg_cost = f"Actual Cost: ${round(actual_cost,2)}\n"
    msg_cbrk = f"Cost Breakdown:\n{components}\n"

    print(msg_date, msg_cost, msg_cbrk)

  if actual_cost > budget_amount:
    print("we are over budget!!..")
    
    slack_payload={
      # "channel": "#datadog-alerts",
      "text": f"Hello @{user},\nYour Datadog Budget has exceeded the budget amount of ${budget_amount} for current month by ${round(actual_cost-budget_amount,2)}\n",
      "attachments": [
        {
          "fallback":"Open <https://app.datadoghq.com/billing/usage|Datadog Billing & Usage Page> for details!",
          "pretext":msg_date,
          "color": "#632CA6",
          "fields": [
              {
                "title": msg_cost,
                "value": msg_cbrk,
                "short": "false"
              }
          ]
        }
      ]
    }

    print(slack_payload)

    request = post(slack_webhook_url, json.dumps(slack_payload))
    
    print("channel notified!")

  else:    
    slack_payload={
      "channel": "#datadog-alerts",
      "text": f"Hello @{user},\nYour Datadog spent is ${actual_cost}, which is below the budget amount of ${budget_amount} set for this month.\n",
      "attachments": [
        {
          "fallback":"Open <https://app.datadoghq.com/billing/usage|Datadog Billing & Usage Page> for details!",
          "pretext":msg_date,
          "color": "#632CA6",
          "fields": [
              {
                "title": msg_cost,
                "value": msg_cbrk,
                "short": "false"
              }
          ]
        }
      ]
    }

    print(slack_payload)

    request = post(slack_webhook_url, json.dumps(slack_payload))
    
    print(f"We are still under the budget. All good!")

# billing(None,None)
