import time
from config import GRID_WIDTH, GRID_HEIGHT

class Communicator:
    def __init__(self, true_map, use_rl_prediction=False):
        self.true_map = true_map
        self.use_rl_prediction = use_rl_prediction
        self.perceived_map = {
            "obstacles": [row[:] for row in true_map["obstacles"]],
            "safety": [row[:] for row in true_map["safety"]],
            "hazards": [row[:] for row in true_map["hazards"]],
            "sight": [row[:] for row in true_map["sight"]],
            "timestamps": [[None for _ in range(GRID_HEIGHT)] for _ in range(GRID_WIDTH)],
            "confidence": [[0 for _ in range(GRID_HEIGHT)] for _ in range(GRID_WIDTH)]
        }

    def update_from_report(self, report):
        """
        Update perceived map based on a report (from a drone or agent).
        """
        for (i, j), cell_info in report.items():
            self.perceived_map["timestamps"][i][j] = cell_info["timestamp"]
            self.perceived_map["confidence"][i][j] = cell_info["confidence"]

    def decay_confidence(self, decay_rate=0.05):
        """
        Decay confidence in cells based on time elapsed.
        """
        current_time = time.time()
        for i in range(GRID_WIDTH):
            for j in range(GRID_HEIGHT):
                ts = self.perceived_map["timestamps"][i][j]
                if ts is not None:
                    elapsed = current_time - ts
                    self.perceived_map["confidence"][i][j] = max(0, self.perceived_map["confidence"][i][j] - decay_rate * elapsed)

    def predict_cell(self, i, j):
        """
        Predict cell state if never updated.
        """
        if self.use_rl_prediction:
            predicted_state = self.perceived_map["hazards"][i][j]  # Stub for RL prediction.
        else:
            predicted_state = self.perceived_map["hazards"][i][j]
        return predicted_state

    def update_perceived_map(self):
        """
        Update the perceived map: decay confidence and predict cells with no update.
        """
        self.decay_confidence()
        for i in range(GRID_WIDTH):
            for j in range(GRID_HEIGHT):
                if self.perceived_map["timestamps"][i][j] is None:
                    self.perceived_map["hazards"][i][j] = self.predict_cell(i, j)
