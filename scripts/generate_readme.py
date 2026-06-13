import os
import json
import requests
import feedparser
import datetime
from dateutil import parser as date_parser

CACHE_FILE = "scripts/cache.json"

def load_cache():
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "github_stats": {},
            "leetcode_stats": {},
            "medium_posts": [],
            "github_activity": []
        }

def save_cache(cache_data):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache_data, f, indent=2)

def fetch_github_activity(username, token):
    headers = {"Authorization": f"token {token}"} if token else {}
    try:
        url = f"https://api.github.com/users/{username}/events/public"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        events = response.json()

        recent_activity = []
        for event in events:
            if len(recent_activity) >= 5:
                break
            repo_name = event.get("repo", {}).get("name", "unknown")
            event_type = event.get("type")

            activity_str = ""
            if event_type == "PushEvent":
                commits = event.get("payload", {}).get("commits", [])
                commit_count = len(commits)
                activity_str = f"🚀 Pushed {commit_count} commit(s) to {repo_name}"
            elif event_type == "WatchEvent":
                activity_str = f"⭐ Starred {repo_name}"
            elif event_type == "PullRequestEvent":
                action = event.get("payload", {}).get("action", "opened")
                activity_str = f"🔀 {action.capitalize()} PR in {repo_name}"
            elif event_type == "IssuesEvent":
                action = event.get("payload", {}).get("action", "opened")
                activity_str = f"📝 {action.capitalize()} issue in {repo_name}"
            elif event_type == "CreateEvent":
                ref_type = event.get("payload", {}).get("ref_type", "repository")
                activity_str = f"🎉 Created {ref_type} {repo_name}"
            elif event_type == "ForkEvent":
                activity_str = f"🍴 Forked {repo_name}"
            else:
                continue # Skip other events for brevity

            recent_activity.append(activity_str)

        return recent_activity
    except Exception as e:
        print(f"Error fetching GitHub activity: {e}")
        return None

def fetch_leetcode_stats(username):
    url = "https://leetcode.com/graphql"
    query = """
    query getUserProfile($username: String!) {
        matchedUser(username: $username) {
            submitStats: submitStatsGlobal {
                acSubmissionNum {
                    difficulty
                    count
                }
            }
        }
    }
    """
    variables = {"username": username}
    try:
        response = requests.post(url, json={"query": query, "variables": variables}, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Error fetching LeetCode stats: {e}")
        return None

def fetch_medium_posts(username):
    feed_url = f"https://medium.com/feed/@{username}"
    try:
        feed = feedparser.parse(feed_url)
        posts = []
        for entry in feed.entries[:3]:
            # Convert published date to short format
            pub_date = "Unknown Date"
            if hasattr(entry, "published"):
                try:
                    dt = date_parser.parse(entry.published)
                    pub_date = dt.strftime("%b %d, %Y")
                except Exception:
                    pub_date = entry.published

            posts.append({
                "title": entry.title,
                "url": entry.link,
                "date": pub_date
            })
        return posts
    except Exception as e:
        print(f"Error fetching Medium posts: {e}")
        return None


def generate_readme_content(user_name, github_username, leetcode_username, github_activity, medium_posts):
    # 1. Hero Banner
    hero_banner = f"""<div align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=30&pause=1000&color=2196F3&center=true&vCenter=true&width=600&lines=Hi,+I'm+{user_name};AI%2FML+Engineer+%7C+Open+Source+%7C+Research" alt="Typing SVG" />
</div>
"""

    # 2. About Me block
    about_me = """
## 👨‍💻 About Me
- 🔭 I'm currently working on exciting AI/ML projects and open-source contributions.
- 🌱 I'm currently learning advanced machine learning architectures and distributed systems.
- 👯 I'm looking to collaborate on innovative open-source AI tools.
- 📫 How to reach me: Connect with me on LinkedIn or Twitter.
"""

    # 3. GitHub Stats Row
    github_stats_row = f"""
<div align="center">
  <table>
    <tr>
      <td align="center">
        <img src="https://github-readme-stats.vercel.app/api?username={github_username}&show_icons=true&theme=dark&hide_border=true&bg_color=0d1117" alt="GitHub Stats" />
      </td>
      <td align="center">
        <img src="https://github-readme-streak-stats.herokuapp.com/?user={github_username}&theme=dark&hide_border=true&background=0d1117" alt="GitHub Streak" />
      </td>
      <td align="center">
        <img src="https://github-readme-stats.vercel.app/api/top-langs/?username={github_username}&layout=compact&theme=dark&hide_border=true&bg_color=0d1117" alt="Top Languages" />
      </td>
    </tr>
  </table>
</div>
"""

    # 4. LeetCode Stats Card
    leetcode_stats_card = f"""
<div align="center">
  <a href="https://leetcode.com/{leetcode_username}">
    <img src="https://leetcard.jacoblin.cool/{leetcode_username}?theme=dark&font=Nunito&ext=activity" alt="LeetCode Stats" />
  </a>
</div>
"""

    # 5. Recent Blog Posts Section
    blog_posts_section = "\n## 📝 Latest Writing\n\n"
    if medium_posts:
        for post in medium_posts:
            blog_posts_section += f"- [{post['title']}]({post['url']}) - *{post['date']}*\n"
    else:
        blog_posts_section += "- No recent posts found.\n"

    # 6. Recent GitHub Activity
    activity_section = "\n## ⚡ Recent GitHub Activity\n\n"
    if github_activity:
        for activity in github_activity:
            activity_section += f"- {activity}\n"
    else:
        activity_section += "- No recent public activity.\n"

    # 7. Tech Stack Badges
    tech_stack = """
## 🛠️ Tech Stack

<div align="center">

### Languages
<img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/C++-00599C?style=flat-square&logo=c%2B%2B&logoColor=white" />
<img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black" />
<img src="https://img.shields.io/badge/SQL-4479A1?style=flat-square&logo=postgresql&logoColor=white" />

### ML/AI Frameworks
<img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white" />
<img src="https://img.shields.io/badge/TensorFlow-FF6F00?style=flat-square&logo=tensorflow&logoColor=white" />
<img src="https://img.shields.io/badge/Scikit_Learn-F7931E?style=flat-square&logo=scikit-learn&logoColor=white" />
<img src="https://img.shields.io/badge/Hugging_Face-FFAA00?style=flat-square&logo=huggingface&logoColor=white" />

### Tools & Infra
<img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white" />
<img src="https://img.shields.io/badge/Git-F05032?style=flat-square&logo=git&logoColor=white" />
<img src="https://img.shields.io/badge/Linux-FCC624?style=flat-square&logo=linux&logoColor=black" />
<img src="https://img.shields.io/badge/AWS-232F3E?style=flat-square&logo=amazonaws&logoColor=white" />

</div>
"""

    # 8. Footer
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    footer = f"""
---
<div align="center">
  <p><i>Auto-updated daily via GitHub Actions | Last updated: {timestamp}</i></p>
</div>
"""

    # Combine all parts
    readme_content = f"{hero_banner}{about_me}{github_stats_row}{leetcode_stats_card}{blog_posts_section}{activity_section}{tech_stack}{footer}"

    return readme_content

def update_readme(content):
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

# Update main function to call these new functions

def main():
    # Load cache
    cache = load_cache()

    # Environment variables
    github_token = os.environ.get("GITHUB_TOKEN")
    user_name = os.environ.get("USER_NAME") or "Christin"
    github_username = os.environ.get("GITHUB_USERNAME") or "freebooter1052"
    leetcode_username = os.environ.get("LEETCODE_USERNAME") or "christinjb100"
    medium_username = os.environ.get("MEDIUM_USERNAME") or "christinjb100"

    # Fetch Data with Fallbacks
    print("Fetching GitHub Activity...")
    github_activity = fetch_github_activity(github_username, github_token)
    if github_activity is not None:
        cache["github_activity"] = github_activity
    else:
        print("Using cached GitHub Activity.")
        github_activity = cache.get("github_activity", [])

    print("Fetching LeetCode Stats...")
    leetcode_stats = fetch_leetcode_stats(leetcode_username)
    if leetcode_stats is not None:
        cache["leetcode_stats"] = leetcode_stats
    else:
        print("Using cached LeetCode Stats.")
        leetcode_stats = cache.get("leetcode_stats", {})

    print("Fetching Medium Posts...")
    medium_posts = fetch_medium_posts(medium_username)
    if medium_posts is not None:
        cache["medium_posts"] = medium_posts
    else:
        print("Using cached Medium Posts.")
        medium_posts = cache.get("medium_posts", [])

    # Save updated cache
    save_cache(cache)


    # Generate README content
    readme_content = generate_readme_content(user_name, github_username, leetcode_username, github_activity, medium_posts)

    # Write to README.md
    update_readme(readme_content)
    print("README.md updated successfully!")

if __name__ == "__main__":
    main()
