# Discord Giveaway Bot
![Image](https://github.com/user-attachments/assets/5f2145da-28d6-4831-854c-f680627599fa)

[![GitHub](https://img.shields.io/badge/GitHub-ReizoZ-blue?style=flat-square&logo=github)](https://github.com/ReizoZ) [![Ko-fi](https://img.shields.io/badge/Ko--fi-ReizoZ-ff5e5b?style=flat-square&logo=ko-fi)](https://ko-fi.com/E1E41CVWBU) [![Discord](https://img.shields.io/badge/Discord-Invite%20Bot-%235865F2?style=flat-square&logo=discord)](https://discord.com/oauth2/authorize?client_id=1358819912445067370&permissions=1689934340028480&integration_type=0&scope=bot)

A comprehensive Discord bot for creating, managing, and participating in giveaways within your server, featuring an interactive interface and a web view for giveaway summaries.

## Features

*   **Easy Giveaway Creation:** Use the `/giveaway` slash command to launch a modal and set up your giveaway details (prize, number of winners, duration, description, optional image).
*   **Interactive Participation:** Users can enter giveaways by clicking a "🎉" button on the giveaway message.
*   **Real-time Updates:** The giveaway message embed updates automatically with the remaining time and current entry count.
*   **Automatic Winner Selection:** Winners are randomly selected from the participants when the timer ends.
*   **Winner Announcements:** Winners are announced in the channel and receive a direct message notification.
*   **Reroll Functionality:** Easily reroll winners for a completed giveaway using the `/reroll` command or by right-clicking the giveaway message and selecting "Reroll Giveaway".
*   **Persistent Storage:** Giveaway details, participants, and winners are stored in an SQLite database.
*   **Web Summary:** Each completed giveaway has a dedicated web page (hosted by the included Flask app) showing a summary (host, prize, winners, participants, etc.). The link is added to the giveaway message upon completion.
*   **Cancellation:** Hosts can cancel an ongoing giveaway.
*   **Leave Option:** Participants can leave a giveaway after entering.
*   **Docker Support:** Includes a `Dockerfile` for easy containerization and deployment.

## Commands

*   `/giveaway [image]`: Starts the process to create a new giveaway. Optionally attach an image file.
*   `/reroll <giveaway_id> [number_of_winners]`: Rerolls winners for a specific giveaway message ID. Defaults to 1 winner if not specified. Requires host or admin permissions.
*   **Context Menu -> Reroll Giveaway**: Right-click on a completed giveaway message to reroll the original number of winners. Requires host or admin permissions.

## Web Interface

The project includes a simple Flask web application (`app.py`) that serves a summary page for each giveaway. After a giveaway ends, a button linking to this summary page (e.g., `yourdomain.com/message_id`) is added to the original giveaway message in Discord.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ReizoZ/GiftMaster.git
    cd GiftMaster
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Environment Variables:**
    *   Copy `.env.example` to `.env`.
    *   Fill in the required values in the `.env` file:
        *   `DISCORD_TOKEN`: Your Discord bot token.
        *   `DOMAIN`: The base URL where the Flask web app will be hosted (e.g., `http://localhost:5000` or `https://yourdomain.com`). This is used for the summary links.

5.  **Run the Bot:**
    ```bash
    python bot.py
    ```
6.  **Run the Web App (in a separate terminal):**
    ```bash
    python app.py
    ```
    *(Note: The `Dockerfile` combines these into a single container)*

## Docker Deployment

1.  **Build the Docker image:**
    ```bash
    docker build -t giveaway-bot .
    ```
2.  **Run the Docker container:**
    ```bash
    docker run -d --env-file .env -p 5000:5000 --name giveaway-bot-container giveaway-bot
    ```
    *(Ensure your `.env` file is correctly populated before running)*

*(See `captain-definition` for potential CapRover deployment configurations.)*

## Dependencies

*   discord.py
*   Flask
*   python-dotenv
*   aiohttp (usually included with discord.py)
*   aiosqlite (or standard `sqlite3`)

## License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.
