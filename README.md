# UW Quad Rescue Simulation

This project simulates a rescue mission in the University of Washington Quad, where an autonomous agent navigates a grid-based map to locate a victim and safely evacuate them, avoiding hazards like fire zones.

## 📁 Project Structure

- `main.py`: Runs the simulation
- `config.py`: Grid settings and constants
- `map.py`: Defines the UW Quad grid layout
- `pathfinding.py`: Pathfinding logic (A*, etc.)
- `agent.py`: Agent behavior and movement
- `commander.py`: Coordinates simulation flow
- `drl_pathfinding_env.py`: Environment logic

## 🛠️ Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/SDAIC-Hackathon-Code.git
cd SDAIC-Hackathon-Code
```

### 2. Create a Virtual Environment (Optional)

```bash
python -m venv venv
source venv/bin/activate     # macOS/Linux
venv\Scripts\activate        # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## ▶️ Run the Simulation

```bash
python main.py
```

## 🎨 Color Legend

- 🟦 **Blue**: Agent (robots or drones)
- 🟥 **Red**: Fire zones
- ⬛ **Black**: Blockers or obstacles
- 🟩 **Green**: Exit points
- 🟨 **Yellow**: Victims
## 📬 Questions?

Feel free to collaborate or open issues!
