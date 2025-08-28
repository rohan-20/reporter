import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta, UTC
from ascii import display_banner
from config import save_token, load_token, save_api, load_api
from groq import Groq, PermissionDeniedError, APIStatusError

def get_github_token():
    token = load_token()
    if not token:
        print("🔑 No GitHub token found.")
        token = input("👉 Enter your GitHub Personal Access Token (PAT): ")
        save_token(token)
    return token

def get_api():
    api = load_api()
    if not api:
        print("No Groq API Key found.")
        api = input("👉 Enter your Groq API Key:")
        save_api(api)
    return Groq(api_key=api)


def main():

    load_dotenv()
    # -------------------------------
    # ASCII Banner
    # -------------------------------
    display_banner()


    # -------------------------------
    # Load Environment
    # -------------------------------
    token = get_github_token()
    client = get_api()

    # -------------------------------
    # Prompt User for Inputs
    # -------------------------------
    github_user = input("👤 Enter your GitHub username: ").strip()
    repo_name = input("📦 Enter the repository (format: owner/repo): ").strip()
    days = input("📅 Enter number of days to look back (default=1): ").strip()
    days = int(days) if days.isdigit() else 1

    # -------------------------------
    # GitHub Helpers
    # -------------------------------
    def fetch_commit_diffs(repo, sha):
        """Fetch file diffs for a commit, excluding noise."""
        url = f"https://api.github.com/repos/{repo}/commits/{sha}"
        headers = {"Authorization": f"token {token}"}
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()

        diffs = []
        for file in data.get("files", []):
            filename = file["filename"]

            # Skip noisy files
            if any(filename.endswith(ext) for ext in [".lock", ".md", ".txt", ".png", ".jpg", ".jpeg", ".svg"]):
                continue
            if "package-lock.json" in filename or "yarn.lock" in filename:
                continue

            patch = file.get("patch")
            if patch:
                truncated_patch = patch[:500] + ("..." if len(patch) > 500 else "")
                diffs.append(f"File: {filename}\n{truncated_patch}")
        return diffs

    def fetch_commits(repo, days=1):
        """Fetch commits by user within timeframe and include diffs."""
        since = (datetime.now(UTC) - timedelta(days=days)).isoformat()
        url = f"https://api.github.com/repos/{repo}/commits?since={since}"
        headers = {"Authorization": f"token {token}"}

        r = requests.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()

        commits = []
        for c in data:
            if c["commit"]["author"]["name"].lower() == github_user.lower():
                sha = c["sha"]
                message = c["commit"]["message"]
                diffs = fetch_commit_diffs(repo, sha)
                commits.append({
                    "message": message,
                    "diffs": diffs
                })
        return commits

    def generate_summary(commits):
        if not commits:
            return "No diffs found for the given timeframe."

        all_diffs = []
        for c in commits:
            all_diffs.extend(c["diffs"])

        activity_text = "\n\n".join(all_diffs)
        prompt = f"""
You are an assistant that writes daily standup summaries for developers.
Your task is:
- Summarize the changes below in plain English, for teammates at a standup meeting.
- DO NOT copy, quote, or refer to code or diffs. You can ONLY refer to filenames.
- Do NOT reproduce any part of the code diffs in your answer.
- Only describe the type of changes, improvements, bug fixes, or features.
- Start with: 'Yesterday I worked on...'
- Always answer in dashed list and not in paragraphs.

---DIFFS START---
{activity_text}
---DIFFS END---

Write your standup summary below (no code):
Standup:
"""

        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=0.4,
                max_tokens=500,
            )

            result = chat_completion.choices[0].message.content
            if "Standup:" not in result:
                result = "Standup:\n" + result.strip()
            return result   

        except PermissionDeniedError as e:
            return(
                "❌ Access denied while calling Groq API.\n"
                "This often happens if:\n"
                "- You are behind a VPN that blocks Groq\n"
                "- Your API key is invalid or expired\n\n"
                f"Details: {e}"
            )
        
        except APIStatusError as e:
            return f"❌ API error from Groq: {e}"
        
        except Exception as e:
            return f"❌ Unexpected error: {e}"
        

    # -------------------------------
    # Run
    # -------------------------------
    print("🚀 Fetching commits from GitHub...")
    commits = fetch_commits(repo_name, days)

    summary = generate_summary(commits)
    print("\n--- 📊 Auto Standup ---\n")
    print(summary)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting. . .")