#%%
import subprocess
import threading
import time
from inputimeout import inputimeout, TimeoutOccurred

#%% Script metadata
__author__  = "muralivnv"
__version__ = "1.0.9"

#%% util_functions
min_to_sec = lambda x: x*60.0

#%% global setting
## configuration
global_config = {}
global_config['git']                        = "git"
global_config['sync_time_sec']              = min_to_sec(10.0)
global_config['local_commit_wait_time_sec'] = min_to_sec(2.0)

## variables
global_vars = {}
global_vars['kill_script']   = False
global_vars['is_pulling']    = False
global_vars['is_pushing']    = False
global_vars['is_committing'] = False
global_vars['disp_user_controller'] = False
global_vars['is_stdout_released']   = True

git_toplevel_dir = ""

## Constants
CURSOR_UP  = '\033[F'
ERASE_LINE = '\033[K'

#%% setup logging
import logging

class CustomFormatter(logging.Formatter):
  def format(self, record):
    global global_vars
    global_vars['disp_user_controller'] = False
    
    while ( (not global_vars['is_stdout_released']) and (not global_vars['kill_script']) ):
      time.sleep(0.5)

    # remove last user input prompt from stdout
    print(ERASE_LINE + CURSOR_UP)

    message = super(CustomFormatter, self).format(record)
    global_vars['disp_user_controller'] = True
    return message

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s | %(message)s')
logger = logging.getLogger(__name__)
for handler in logger.root.handlers:
  handler.setFormatter(CustomFormatter(handler.formatter._fmt))

#%% unused functions

def init_ssh_agent(sys_os: str)->None:
  ssh_agent_cmd = {}
  ssh_agent_cmd["Linux"] = ["eval", "$(ssh-agent", "-s)"]
  ssh_agent_cmd["Windows"] = ["start-ssh-agent.cmd"]
  
  if (sys_os in ssh_agent_cmd):
    _ = subprocess.run(ssh_agent_cmd[sys_os], shell=True)

def add_ssh_key(sys_os: str, ssh_key: str)->None:
  ssh_add_cmd = "ssh-add"
  if (sys_os == "Windows"):
    # get path where ssh-add is stored
    git_path = subprocess.check_output(["where", "git"])
    git_path = git_path.strip()
    git_path = git_path.decode('utf-8')
    if (any(git_path)):
      path_list = git_path.split('\\')
      ssh_add_path = []
      for path in path_list:
        ssh_add_path.append(path)
        if ("git" in path.lower()):
          break
      ssh_add_path = ssh_add_path + ["usr", "bin"]
      ssh_add_cmd  = '/'.join(ssh_add_path + [ssh_add_cmd])
  
  _ = subprocess.run([ssh_add_cmd, ssh_key], shell=True)

def git_establish_ssh(ssh_key: str)->None:
  import platform
  sys_os = platform.system()
  if ((sys_os == "Linux") or (sys_os == "Windows")):
    init_ssh_agent(sys_os)
    add_ssh_key(sys_os, ssh_key)
  else:
    logging.warn("SSH Key not added, OS is unfamiliar")
  

#%% git utility functions
def log_subprocess_output(out_pipe, err_pipe)->None:
  out_str = b''.join( [line for line in out_pipe] ).strip()
  err_str = b''.join( [line for line in err_pipe] ).strip()

  if (any(out_str)):
    logging.info(out_str.decode('utf-8'))
  
  if (any(err_str)):
    logging.error(err_str.decode('utf-8'))

def get_git_top_level_dir()->str:
  proc = subprocess.Popen([global_config['git'], "rev-parse", "--show-toplevel"], stdout=subprocess.PIPE)
  dir_name = ""
  for line in proc.stdout:
    line = line.strip()
    if (any(line)):
      dir_name = line.decode('utf-8')
      break
  return dir_name

def fetch()->None:
  proc = subprocess.Popen([global_config['git'], "fetch", "--all"], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=git_toplevel_dir)
  log_subprocess_output(proc.stdout, proc.stderr)
  proc.wait()

def pull()->None:
  proc = subprocess.Popen([global_config['git'], "pull", "origin", "main"], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=git_toplevel_dir)
  log_subprocess_output(proc.stdout, proc.stderr)
  proc.wait()

def push()->None:
  proc = subprocess.Popen([global_config['git'], "push", "origin", "main"], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=git_toplevel_dir)
  log_subprocess_output(proc.stdout, proc.stderr)
  proc.wait()

def stage_files(files: list)->None:
  # prepend and append " in case file names have spaces in them
  # files = [f"\"{file}\"" for file in files]

  # main implementation
  add_command = [global_config['git'], "add"] + files
  proc = subprocess.Popen(add_command,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=git_toplevel_dir)
  log_subprocess_output(proc.stdout, proc.stderr)
  proc.wait()

def commit(commit_msg:str)->None:
  proc = subprocess.Popen([global_config['git'], "commit", "-m", commit_msg], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=git_toplevel_dir)
  log_subprocess_output(proc.stdout, proc.stderr)
  proc.wait()

def reset_to_commit(commit_id: str)->None:
  proc = subprocess.Popen([global_config['git'], "reset", "--soft", commit_id], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=git_toplevel_dir)
  log_subprocess_output(proc.stdout, proc.stderr)
  proc.wait()

def get_dirty_files()->list:
  dirty_files = []
  proc = subprocess.Popen([global_config['git'], "status", "--porcelain"], 
                           stdout=subprocess.PIPE, cwd=git_toplevel_dir)
  for line in proc.stdout:
    line = line.strip()
    if(any(line)):
      dirty_file = line[line.find(b' '):]
      dirty_file = dirty_file.decode('utf-8').strip()
      dirty_file = dirty_file.replace('"', '')
      dirty_files.append( dirty_file )
  
  return dirty_files

def stash_save(files_to_save: list)->None:
  save_command = [global_config['git'], "stash", "push", "-u"] + files_to_save
  proc = subprocess.Popen(save_command,  
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=git_toplevel_dir)
  log_subprocess_output(proc.stdout, proc.stderr)
  proc.wait()

def stash_apply(stash_name: str) -> None:
  proc = subprocess.Popen([global_config['git'], "stash", "apply", stash_name],  
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=git_toplevel_dir)
  log_subprocess_output(proc.stdout, proc.stderr)
  proc.wait()

def compute_git_hash()->str:
  staged_changes_proc = subprocess.Popen([global_config['git'], "status", "-v"], stdout=subprocess.PIPE, cwd=git_toplevel_dir)
  hash_proc = subprocess.Popen([global_config['git'], "hash-object", "--stdin"], stdin=staged_changes_proc.stdout, 
                                stdout=subprocess.PIPE, cwd=git_toplevel_dir)
  for line in hash_proc.stdout:
    line = line.strip()
    if (any(line)):
      return line.decode('utf-8')
  return ""

def get_local_commits() -> (bool, list):
  commits_info = []
  has_commits = False

  proc = subprocess.Popen([global_config['git'], "log", "origin/main..HEAD", "--oneline"], stdout=subprocess.PIPE, cwd=git_toplevel_dir)
  for line in proc.stdout:
    line = line.strip()
    if (any(line)):
      line = line.decode('utf-8')
      commits_info.append(line)
      has_commits = True
    
  return has_commits, commits_info

def is_pull_req()->bool:
  fetch()
  proc = subprocess.Popen([global_config['git'], "log", "HEAD..origin/main", "--oneline"], 
                           stdout=subprocess.PIPE)
  remote_has_commits = False

  for line in proc.stdout:
    line = line.strip()
    if (any(line)):
      line = line.decode('utf-8')
      remote_has_commits = True
      break
  return remote_has_commits

def squash_commits(commits_info: list)->None:
  if (len(commits_info) > 1):
    local_commits_hash = []
    for commit_info in commits_info:
      tmp        = commit_info.split(' ')
      hash_str   = tmp[0]
      local_commits_hash.append( hash_str )
    
    if (any(local_commits_hash)):
      logging.info(f"squashed commits {','.join(local_commits_hash)} onto HEAD~{len(local_commits_hash)}")
      reset_to_commit(f"HEAD~{len(local_commits_hash)}")
      commit_hash = compute_git_hash()
      commit(f"sync -- #{commit_hash}")

#%% Git Pull/Push thread utils

class CustomTimer:
  last_update_time_ = 0.0
  timer_limit_      = 0.0     
  def __init__(self, timespan_limit):
    self.timer_limit_ = timespan_limit
    self.last_update_time_ = time.time()
  
  def has_exceeded_limit(self)->bool:
    time_now = time.time()
    if ( (time_now - self.last_update_time_) > self.timer_limit_ ):
      return True
    return False
  
  def reset(self)->None:
    self.last_update_time_ = time.time()

def pull_helper():
  global global_vars
  if (is_pull_req() == True):
    global_vars['is_pulling'] = True

    logging.info("pulling from origin")
    dirty_files = get_dirty_files()
    if (any(dirty_files)):
      logging.info("local repo is dirty stashing temporarily under stash@{0}")
      stash_save(dirty_files)

    pull()

    if (any(dirty_files)):
      logging.info("adding back local changes from stash@{0}")
      stash_apply("stash@{0}")
    
    global_vars['is_pulling'] = False

def push_helper():
  global global_vars

  has_local_commits, commits_info = get_local_commits()
  if (has_local_commits == True):
    global_vars['is_pushing'] = True  
    squash_commits(commits_info)

    logging.info("pushing to origin")
    push()

    global_vars['is_pushing'] = False

def commit_helper():
  global global_vars
  dirty_files = get_dirty_files()
  if (any(dirty_files)):
    global_vars['is_committing'] = True
    stage_files(dirty_files)
    commit_hash = compute_git_hash()
    logging.info(f"committing with message - \"sync -- #{commit_hash}\"")
    commit(f"sync -- #{commit_hash}")
    global_vars['is_committing'] = False

def pull_from_origin()->None:
  timer = CustomTimer(global_config['sync_time_sec'])

  pull_helper()
  while(global_vars['kill_script'] == False):
    if ( (timer.has_exceeded_limit()) and 
         (global_vars['is_committing'] == False) and 
         (global_vars['is_pushing']    == False) ):
      
      pull_helper()
      timer.reset()
    time.sleep(5.0)

def push_to_origin()->None:
  timer = CustomTimer(global_config['sync_time_sec'])

  while(global_vars['kill_script'] == False):
    if ( ( timer.has_exceeded_limit() ) and
        (global_vars['is_pulling'] == False) and 
        (global_vars['is_committing'] == False)):
      
      push_helper()      
      timer.reset()
    time.sleep(5.0)

def commit_if_req()->None:
  try:
    while( (global_vars['is_pulling'] == True) or (global_vars['is_pushing'] == True) ):
      time.sleep(1.0)
      if (global_vars['kill_script'] == True):
        return
  except:
    return
  
  commit_helper()

def handle_user_input(user_input: str)->None:
  if (user_input == '1'):
    push_helper()
  elif (user_input == '2'):
    pull_helper()
  elif (user_input == '3'):
    commit_helper()
  else:
    print("unknown command, check input")

def user_control()->None:
  global global_vars
  while(global_vars['kill_script'] == False):
    if (global_vars['disp_user_controller'] == True):
      global_vars['is_stdout_released'] = False
      try:
        user_input = inputimeout(prompt="1[push], 2[pull], 3[commit] >> ", timeout=5)
        global_vars['is_stdout_released'] = True
        handle_user_input(user_input)
      except TimeoutOccurred:
        # remove last user input prompt from stdout
        print(CURSOR_UP + ERASE_LINE + CURSOR_UP)
      except:
        pass
    else:
      global_vars['is_stdout_released'] = True
      time.sleep(0.1)
      

#%% Main
def main():
  global global_vars, git_toplevel_dir
  pull_thread = threading.Thread(target=pull_from_origin)
  push_thread = threading.Thread(target=push_to_origin)
  user_control_thread = threading.Thread(target=user_control)

  git_toplevel_dir = get_git_top_level_dir()
  logging.info("initiated sync")

  try:
    pull_thread.start()
    time.sleep(5.0)
    push_thread.start()
    commit_if_req()

    user_control_thread.start()

    commit_timer = CustomTimer(global_config['local_commit_wait_time_sec'])
    while(global_vars['kill_script'] == False):
      if (commit_timer.has_exceeded_limit()):
        commit_if_req()
        commit_timer.reset()
      time.sleep(10.0)

    pull_thread.join()
    push_thread.join()
  except KeyboardInterrupt:
    global_vars['kill_script'] = True
    pull_thread.join()
    push_thread.join()
    user_control_thread.join()
  except:
    global_vars['kill_script'] = True
    pull_thread.join()
    push_thread.join()
    user_control_thread.join()
    logging.exception("exception occured")

  logging.info("closing sync, goodbye!")

if __name__ == '__main__':
  main()