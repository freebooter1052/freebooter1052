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
                payload = event.get("payload", {})
                commits = payload.get("commits", [])
                commit_count = payload.get("size")
                if commit_count is None:
                    commit_count = len(commits)
                if commit_count == 0 and payload.get("before") and payload.get("head"):
                    try:
                        compare_url = f"https://api.github.com/repos/{repo_name}/compare/{payload['before']}...{payload['head']}"
                        cmp_res = requests.get(compare_url, headers=headers, timeout=5)
                        if cmp_res.status_code == 200:
                            commit_count = cmp_res.json().get("total_commits", 1)
                        else:
                            commit_count = 1
                    except Exception:
                        commit_count = 1
                elif commit_count == 0:
                    commit_count = 1
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

def check_github_stats_api(github_username):
    url = f"https://github-readme-stats-fast.vercel.app/api?username={github_username}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return False
        if "Something went wrong" in response.text:
            return False
        return True
    except Exception as e:
        print(f"Error checking GitHub stats API: {e}")
        return False

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


import re

def generate_stats_content(github_username, leetcode_username, github_api_ok):
    github_stats_html = f"""
<div align="center">
  <table>
    <tr>
      <td align="center">
        <img src="https://github-readme-stats-fast.vercel.app/api?username={github_username}&show_icons=true&theme=dark&hide_border=true&bg_color=0d1117" alt="GitHub Stats" />
      </td>
      <td align="center">
        <img src="https://streak-stats.demolab.com/?user={github_username}&theme=dark&hide_border=true&background=0d1117" alt="GitHub Streak" />
      </td>
      <td align="center">
        <img src="https://github-readme-stats-fast.vercel.app/api/top-langs/?username={github_username}&layout=compact&theme=dark&hide_border=true&bg_color=0d1117" alt="Top Languages" />
      </td>
    </tr>
  </table>
</div>
""" if github_api_ok else ""

    leetcode_stats_html = f"""
<div align="center">
  <a href="https://leetcode.com/{leetcode_username}">
    <img src="https://leetcard.jacoblin.cool/{leetcode_username}?theme=dark&font=Nunito&ext=activity" alt="LeetCode Stats" />
  </a>
</div>
"""

    # Combine the blocks, stripping whitespace as needed to ensure no excess spacing
    combined = github_stats_html.strip("\n") + ("\n\n" if github_stats_html else "") + leetcode_stats_html.strip("\n")
    return combined.strip("\n")

def generate_blog_content(medium_posts):
    blog_posts_section = ""
    if medium_posts:
        for post in medium_posts:
            blog_posts_section += f"- [{post['title']}]({post['url']}) - *{post['date']}*\n"
    else:
        blog_posts_section += "- No recent posts found.\n"
    return blog_posts_section.strip("\n")

def generate_activity_content(github_activity):
    activity_section = ""
    if github_activity:
        for activity in github_activity:
            activity_section += f"- {activity}\n"
    else:
        activity_section += "- No recent public activity.\n"
    return activity_section.strip("\n")

def replace_chunk(content, marker, chunk):
    r = re.compile(
        rf"(<!--START:{marker}-->\s*).*?(\s*<!--END:{marker}-->)",
        re.DOTALL,
    )
    if not r.search(content):
        return content
    return r.sub(lambda m: f"{m.group(1)}{chunk.strip()}{m.group(2)}", content)

def update_readme(stats_content, blog_content, activity_content):
    with open("README.md", "r", encoding="utf-8") as f:
        readme_content = f.read()

    new_content = readme_content
    new_content = replace_chunk(new_content, "STATS", stats_content)
    new_content = replace_chunk(new_content, "BLOG", blog_content)
    new_content = replace_chunk(new_content, "ACTIVITY", activity_content)

    # Check for differences in dynamic sections (excluding timestamp)
    if new_content == readme_content:
        print("No changes in dynamic sections. Skipping file update.")
        return False

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_content)
    return True

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

    print("Checking GitHub Stats API...")
    github_api_ok = check_github_stats_api(github_username)
    if not github_api_ok:
        print("GitHub Stats API seems broken. Excluding GitHub stats block.")

    # Generate section contents
    stats_content = generate_stats_content(github_username, leetcode_username, github_api_ok)
    blog_content = generate_blog_content(medium_posts)
    activity_content = generate_activity_content(github_activity)

    # Write to README.md
    updated = update_readme(stats_content, blog_content, activity_content)
    if updated:
        print("README.md updated successfully!")

if __name__ == "__main__":
    main()
