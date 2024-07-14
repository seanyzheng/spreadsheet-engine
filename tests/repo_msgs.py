"""
Does some basic repository linting to ensure best practices for the repo setup 
and commit history.
"""

import subprocess

def test_msgs():
    """
    Ensures all commit messages in the repo history are between 15 and 72 chars 
    in length for non-merge commits
    """
    # Loop through each commit message and check 50/70 rule
    i=0
    while True:
        # Get the commit message
        msg = subprocess.check_output(
            ["git", "log", "-n 1", "--pretty=%B", f"HEAD~{i}"]
            ).strip().decode("utf-8")
        for j, line in enumerate(msg.split("\n")):
            if j == 1:
                assert line == ""
            else:
                if not line.startswith("Merge"):
                    assert len(line) <= 72 and len(line) >= 15
        if msg == "Initial commit/ repository init":
            break
        i += 1


# OMIT THIS TEST FOR NOW, UNTIl SEAN USERNAME ISSUE FIXED
# def test_unique_authors():
#     """
#     Ensures that each email address associated with a commit in the repo is
#     mapped to only one author name
#     """
#     # Get all authors and their emails
#     commits = subprocess.check_output(["git", "log", "--format=%h"]
        # ).strip().decode("utf-8").split("\n")
#     authors = subprocess.check_output(
#         ["git", "log", "--format=%an <%ae>"]
#         ).strip().decode("utf-8").split("\n")
#     # Check for uniqueness
#     author_map = {}
#     for i, author in enumerate(authors):
#         name, email = author.split(" <")
#         email = email[:-1]
#         if email in author_map:
#             try:
#                 assert author_map[email] == name
#             except AssertionError:
#                 print(f"Error: {email} maps to {author_map[email]} and {name}")
#                 print(f"Found at commit #{i}")
#                 print(commits[i])
#                 raise AssertionError
#         else:
#             author_map[email] = name
