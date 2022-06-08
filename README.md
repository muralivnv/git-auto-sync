# Git Auto Sync

A simple script that automatically, at a fixed interval,

- pulls changes from upstream if there any
- commits and pushes changes to upstream
- If there is conflict on pull, automatically fixes it

## Reason

I use Markdown and Obsidian for most of my note-taking. Having to make sure that the notes are properly in sync across multiple devices without relying on external cloud services is a hassle. Given I use git on all of my devices, I thought why not, I don't care about commit messages for my notes as long as the notes and the stuff are in sync.

## Dependency Installation

There is only 1 external package that the script relies on. This dependency can be installed using the following command.

```bash
pip install -r requirements.txt
```

## Using

- Initialize git repo on the folder that requires automatic syncing
- At `<folder-to-sync-location>` open a terminal and run `sync_repo.py` script provided in this repo

First time you execute the script, you will see the following.
![first_time_execution](resources/Pasted%20image%2020220605235648.png)

An additional user interaction is baked into the script so that,

- If a user is done with his/her work but the changes haven't been pushed to upstream or haven't been committed yet, he/she can do quickly by just inputting 3 - to commit, then 1 - to push

## Configuration

The script has following timeouts harcoded at the top as a global variable.

- interval at which script should perform a commit - every `2` min
![commit_interval_loc](resources/Pasted%20image%2020220606000450.png)

- interval at which script should perform a fetch & pull - every `10` min
![fetch_interval_loc](resources/Pasted%20image%2020220606000522.png)

Although, these parameters can be added as script command line arguments, I was lazy to do so.
