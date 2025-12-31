# system_agent.py
import json, time, os, subprocess

class SystemObserverAgent:
    def __init__(self, memory_file="system_memory.json"):
        # Put memory file in a shared location if needed, 
        # but defaulting to local for simplicity as requested.
        self.memory_file = memory_file
        self.mem = self.load()

    def load(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    return json.load(f)
            except:
                pass
        return {"events": []}

    def save(self):
        with open(self.memory_file, "w") as f:
            json.dump(self.mem, f, indent=2)

    def snapshot(self):
        # Extract basic system stats
        cpu = subprocess.getoutput("uptime")
        disk = subprocess.getoutput("df -h / | tail -1")
        event = {
            "time": time.time(),
            "cpu": cpu,
            "disk": disk
        }
        self.mem["events"].append(event)
        # Keep only last 20 events to remain "lightweight"
        self.mem["events"] = self.mem["events"][-20:]
        self.save()

if __name__ == "__main__":
    # Ensure current directory or specified path is used
    agent = SystemObserverAgent(memory_file="/app/memory_db/system_memory.json" if os.path.exists("/app") else "system_memory.json")
    print("🚀 System Observer Agent started...")
    while True:
        agent.snapshot()
        time.sleep(60)
