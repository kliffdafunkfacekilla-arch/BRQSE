# BRQSE Engine (Shadowfall)

**BRQSE** is an AI-First TTRPG Engine designed to facilitate immersive, tactical gameplay with a dual-screen architecture. It combines a robust Python-based combat backend with a dynamic React-based frontend visualization.

![Engine Preview](Web_ui/public/tiles/floor_stone.png) *Placeholder for Engine Screenshot*

## 🌟 Key Features

### 🧠 Dual-Screen AI Architecture
- **Game Master (Backend)**: An AI-driven GM loop that narrates story, resolves player intent, and manages world state.
- **Player View (Frontend)**: A real-time visual interface displaying the battle arena, character stats, and combat logs.

### ⚔️ Tactical Combat System
- **Deep Mechanics**: Fully implemented Turn-Based combat with Initiative, Action Economy (Standard/Bonus), and Status Effects.
- **Advanced Tactics**:
  - **Flanking (2v1)**: Defenders suffer penalties when engaged by multiple foes.
  - **Mobbing (3v1)**: Attackers gain Advantage against overwhelmed targets.
  - **Friendly Fire**: Ranged attacks into melee have a 50% chance to hit allies on a miss.
  - **Cover & Hazards**: Terrain plays a huge role—hide behind Walls or push enemies into Fire/Ice.
- **Species Skills**: Unique mechanical abilities for various species (Reptile Thermal-Gaze, Aquatic Tsunami, Avian Dive-Bomb, Plant Photosynthesis).

### 🎨 Visual Replay System
- **Replay Visualization**: Combat is simulated in the backend and exported as a structured JSON replay.
- **Asset Integration**: The frontend renders rich pixel-art assets for walls, floors, water, and characters, moving beyond simple grid colors.
- **Event Log**: A detailed combat log tracks every roll, damage die, and tactical trigger.

## 📂 Project Structure

- **`brqse_engine/`**: The Core Python package.
  - `combat/`: CombatEngine, Combatant, AI Logic.
  - `abilities/`: EffectRegistry (Skill/Spell handlers).
  - `models/`: Character and Item data models.
- **`Web_ui/`**: The Frontend React Application.
  - `src/components/Arena.tsx`: The main battle visualizer.
  - `public/`: Asset store (tiles, tokens, effects).
- **`Data/`**: CSV and JSON Configuration files.
  - `Species_Skills.csv`: Definitions for all species abilities.
  - `Tactical_Situations.csv`: Rules for combat modifiers.
- **`scripts/`**: Utility scripts.
  - `simple_api.py`: The lightweight API server linking Frontend and Backend.
  - `generate_replay.py`: Simulation script to test combat and generate replays.

## 🚀 Getting Started

### Prerequisites
- **Python 3.8+**
- **Node.js 16+** & **npm**

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-username/brqse-engine.git
    cd brqse-engine
    ```

2.  **Setup Backend**
    *   No complex pip install is required if running locally, just ensure standard libs are present.
    *   (Optional) Create a virtual environment:
        ```bash
        python -m venv venv
        source venv/bin/activate  # On Windows: venv\Scripts\activate
        ```

3.  **Setup Frontend**
    ```bash
    cd Web_ui
    npm install
    ```

### ▶️ Running the Engine

You typically run the backend API and the frontend dev server simultaneously.

**1. Start the API / Simulation**
```bash
# In the root directory
python scripts/simple_api.py
```
*   *Alternatively, to run a single combat simulation:* `python scripts/generate_replay.py`

**2. Start the Frontend**
```bash
# In Web_ui/ directory
npm run dev
```
Open your browser to the URL shown (usually `http://localhost:5173`).

## 🧪 Testing

To verify mechanical interactions:

- **Tactical Rules**: Run `python test_tactics.py` to see a CLI simulation of Flanking and Friendly Fire.
- **Combat Logic**: Run `python test_combat.py` for a basic 1v1 duel test.

## 🤝 Contributing
1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---
*Built with ❤️ by the BRQSE Team*
