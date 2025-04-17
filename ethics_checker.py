class EthicsChecker:
    def __init__(self):
        self.max_risk_threshold = 50  # Example threshold

    def check_decision(self, task):
        """
        Check the ethical implications of a task.
        If risk to the rescuer is too high, require human intervention.
        """
        agent = task['agent']
        rescuer_risk = 100 - agent.remaining_life  # Simplified risk metric.
        if rescuer_risk > self.max_risk_threshold:
            approved = self.human_intervention(task)
            return approved
        return task

    def human_intervention(self, task):
        """
        Simulate human decision intervention.
        """
        print("Ethics Checker flagged task:")
        print(task)
        decision = input("Approve this task? (y/n): ")
        if decision.lower() == "y":
            return task
        else:
            print("Task rejected by human. Adjusting task score.")
            task['score'] -= 20  # Penalize the task score.
            return task
