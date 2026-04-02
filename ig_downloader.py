import glob
import logging
import os
import re
import shutil

import instaloader

from config import DOWNLOAD_DIR, IG_SESSION_FILE

logger = logging.getLogger(__name__)


class IGDownloader:
    def __init__(self):
        self.download_dir = DOWNLOAD_DIR
        os.makedirs(self.download_dir, exist_ok=True)

        self.loader = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            post_metadata_txt_pattern="",
            max_connection_attempts=3,
            dirname_pattern=os.path.join(self.download_dir, "{target}"),
            filename_pattern="{date_utc}_UTC_{shortcode}",
            quiet=True,
        )

        self._login()

    def _login(self):
        session_file = IG_SESSION_FILE
        if session_file and os.path.exists(session_file):
            try:
                self.loader.load_session_from_file(
                    os.path.basename(session_file).replace("session", "").strip("_") or "user",
                    session_file,
                )
                logger.info("Session loaded from %s", session_file)
            except Exception as e:
                logger.error("Failed to load session: %s", e)
        else:
            logger.warning("No session file found — running as anonymous.")

    def _extract_shortcode(self, url: str) -> str | None:
        match = re.search(
            r"instagram\.com/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)", url
        )
        return match.group(1) if match else None

    def _extract_username(self, url: str) -> str | None:
        # Extract from stories URL
        match = re.search(r"instagram\.com/stories/([^/?#]+)", url)
        if match:
            return match.group(1)
        # Extract from profile URL, excluding reserved paths
        reserved = {"p", "reel", "reels", "tv", "stories", "explore", "accounts", "direct"}
        match = re.search(r"instagram\.com/([^/?#]+)", url)
        if match:
            username = match.group(1)
            if username not in reserved:
                return username
        return None

    def _get_downloaded_files(self, target_dir: str) -> list[str]:
        patterns = ["*.jpg", "*.jpeg", "*.png", "*.mp4", "*.webp"]
        files = []
        for pattern in patterns:
            files.extend(glob.glob(os.path.join(target_dir, pattern)))
        return sorted(files)

    def _cleanup(self, target_dir: str):
        try:
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
                logger.info("Cleaned up directory: %s", target_dir)
        except Exception as e:
            logger.error("Cleanup error for %s: %s", target_dir, e)

    def download_post(self, url: str) -> dict:
        shortcode = self._extract_shortcode(url)
        if not shortcode:
            return {"success": False, "error": "Invalid post URL — cannot extract shortcode."}

        target_dir = os.path.join(self.download_dir, shortcode)
        os.makedirs(target_dir, exist_ok=True)

        try:
            logger.info("Downloading post shortcode=%s", shortcode)
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            self.loader.dirname_pattern = target_dir
            self.loader.download_post(post, target=target_dir)

            files = self._get_downloaded_files(target_dir)
            caption = post.caption or ""
            owner = post.owner_username
            media_type = "video" if post.is_video else "photo"
            if post.typename == "GraphSidecar":
                media_type = "carousel"

            logger.info("Post downloaded: %d file(s) from @%s", len(files), owner)
            return {
                "success": True,
                "files": files,
                "caption": caption,
                "owner": owner,
                "type": media_type,
                "target": target_dir,
            }
        except instaloader.exceptions.InstaloaderException as e:
            logger.error("InstaloaderException downloading post %s: %s", shortcode, e)
            self._cleanup(target_dir)
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error("Error downloading post %s: %s", shortcode, e)
            self._cleanup(target_dir)
            return {"success": False, "error": str(e)}

    def download_stories(self, url: str) -> dict:
        username = self._extract_username(url)
        if not username:
            return {"success": False, "error": "Invalid stories URL — cannot extract username."}

        target_dir = os.path.join(self.download_dir, f"stories_{username}")
        os.makedirs(target_dir, exist_ok=True)

        try:
            logger.info("Downloading stories for @%s", username)
            profile = instaloader.Profile.from_username(self.loader.context, username)
            stories = list(self.loader.get_stories(userids=[profile.userid]))

            if not stories:
                self._cleanup(target_dir)
                return {"success": False, "error": f"No active stories found for @{username}."}

            self.loader.dirname_pattern = target_dir
            for story in stories:
                for item in story.get_items():
                    self.loader.download_storyitem(item, target_dir)

            files = self._get_downloaded_files(target_dir)
            if not files:
                self._cleanup(target_dir)
                return {"success": False, "error": f"No story files downloaded for @{username}."}

            logger.info("Stories downloaded: %d file(s) for @%s", len(files), username)
            return {
                "success": True,
                "files": files,
                "caption": f"Stories from @{username}",
                "owner": username,
                "type": "stories",
                "target": target_dir,
            }
        except instaloader.exceptions.InstaloaderException as e:
            logger.error("InstaloaderException downloading stories for @%s: %s", username, e)
            self._cleanup(target_dir)
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error("Error downloading stories for @%s: %s", username, e)
            self._cleanup(target_dir)
            return {"success": False, "error": str(e)}

    def download_profile_pic(self, url: str) -> dict:
        username = self._extract_username(url) or url.strip()
        target_dir = os.path.join(self.download_dir, f"pfp_{username}")
        os.makedirs(target_dir, exist_ok=True)

        try:
            logger.info("Downloading profile picture for @%s", username)
            profile = instaloader.Profile.from_username(self.loader.context, username)
            self.loader.dirname_pattern = target_dir
            self.loader.download_profilepic(profile)

            files = self._get_downloaded_files(target_dir)
            if not files:
                self._cleanup(target_dir)
                return {"success": False, "error": f"Could not download profile picture for @{username}."}

            logger.info("Profile picture downloaded for @%s", username)
            return {
                "success": True,
                "files": files,
                "caption": f"@{username} Profile Picture",
                "owner": username,
                "type": "pfp",
                "target": target_dir,
            }
        except instaloader.exceptions.InstaloaderException as e:
            logger.error("InstaloaderException downloading pfp for @%s: %s", username, e)
            self._cleanup(target_dir)
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error("Error downloading pfp for @%s: %s", username, e)
            self._cleanup(target_dir)
            return {"success": False, "error": str(e)}

    def download_profile_posts(self, username: str, limit: int = 5) -> dict:
        limit = min(limit, 20)
        target_dir = os.path.join(self.download_dir, f"posts_{username}")
        os.makedirs(target_dir, exist_ok=True)

        try:
            logger.info("Downloading %d posts for @%s", limit, username)
            profile = instaloader.Profile.from_username(self.loader.context, username)
            self.loader.dirname_pattern = target_dir
            posts = profile.get_posts()
            downloaded = 0
            for post in posts:
                if downloaded >= limit:
                    break
                self.loader.download_post(post, target=target_dir)
                downloaded += 1

            files = self._get_downloaded_files(target_dir)
            if not files:
                self._cleanup(target_dir)
                return {"success": False, "error": f"No posts found for @{username}."}

            logger.info("Posts downloaded: %d file(s) for @%s", len(files), username)
            return {
                "success": True,
                "files": files,
                "caption": f"Latest {downloaded} posts from @{username}",
                "owner": username,
                "type": "posts",
                "target": target_dir,
            }
        except instaloader.exceptions.InstaloaderException as e:
            logger.error("InstaloaderException downloading posts for @%s: %s", username, e)
            self._cleanup(target_dir)
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error("Error downloading posts for @%s: %s", username, e)
            self._cleanup(target_dir)
            return {"success": False, "error": str(e)}
