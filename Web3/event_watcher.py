from web3utils import get_contract, w3
from config import MY_CONTRACT_ADDRESS, ABI_NAME
import time
from datetime import datetime

def watch_events(event_name, sleep_interval=10):
    my_contract = get_contract(ABI_NAME, MY_CONTRACT_ADDRESS)

    print(f"📡 Listening for event '{event_name}'...\n")
    last_checked = w3.eth.block_number

    while True:
        latest_block = w3.eth.block_number
        if latest_block > last_checked:
            print(f"🔎 Checking new blocks {last_checked+1} to {latest_block}...")

            try:
                # Access to the event
                event_filter = getattr(my_contract.events, event_name)()
                events = event_filter.get_logs(fromBlock=last_checked + 1, toBlock=latest_block)

                for event in events:
                    #example with user parameter
                    user = event['args']['user']
                    print(f"Event by: {user} at {datetime.fromtimestamp(event['args']['timestamp'])}")
            except Exception as e:
                print("⚠️ Error while fetching logs:", e)

            last_checked = latest_block
        time.sleep(sleep_interval)

if __name__ == "__main__":
    try:
        # Exemple : écouter un event nommé "Deposit"
        watch_events("Deposit", sleep_interval=5)
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
