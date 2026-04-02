"""
Helper script to create an Instaloader session file for Instagram login.
Run this script once before starting the bot to enable access to private content.

Usage:
    python create_session.py
"""

import os
import instaloader

SESSION_DIR = "cookies"
SESSION_FILE = os.path.join(SESSION_DIR, "session")


def main():
    os.makedirs(SESSION_DIR, exist_ok=True)

    print("=" * 50)
    print("  Instagram Session Creator")
    print("=" * 50)
    username = input("Instagram username: ").strip()
    password = input("Instagram password: ").strip()

    loader = instaloader.Instaloader()

    try:
        loader.login(username, password)
        loader.save_session_to_file(SESSION_FILE)
        print(f"\n✅ Session saved to: {SESSION_FILE}")
        print("You can now start the bot.")
    except instaloader.exceptions.BadCredentialsException:
        print("\n❌ Login failed: wrong username or password.")
    except instaloader.exceptions.TwoFactorAuthRequiredException:
        code = input("Two-factor authentication code: ").strip()
        try:
            loader.two_factor_login(code)
            loader.save_session_to_file(SESSION_FILE)
            print(f"\n✅ Session saved to: {SESSION_FILE}")
        except Exception as e:
            print(f"\n❌ 2FA login failed: {e}")
    except Exception as e:
        print(f"\n❌ Login failed: {e}")


if __name__ == "__main__":
    main()
