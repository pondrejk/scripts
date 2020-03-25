#!/usr/bin/python
#
# script atomating tasks for revisiting Foreman development setup
#

import os
import subprocess
import sys
import argparse
import git
import time


DB_NAME = 'foreman-db-1'
pwd = os.getcwd() 
fm_dir = pwd + '/foreman'

# parse arguments
parser = argparse.ArgumentParser(description='')
parser.add_argument("-u", "--update-repos",  dest='repos', action='store_true', help="update repositories only" )
args = parser.parse_args()

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

def start_db():
    """Start the database in Docker container"""
    print(color.GREEN + "Starting database container {}".format(DB_NAME) + color.END)
    subprocess.run('docker start {}'.format(DB_NAME), shell=True, check=True)
    print("OK")

def update_repos():
    """Update Foreman and plugins repositories"""
    # list subdirs
    repo_names = [x for x in next(os.walk(pwd))[1]] 
    repo_count = len(repo_names)
    print(color.GREEN + "Updating {} repositories:".format(repo_count) + color.END)
    for repo_name in repo_names:
        t0 = time.time()
        repo_path = pwd + '/' + repo_name
        repo = git.Repo(repo_path)
        if (repo_name == 'foreman'):
            repo.git.checkout('develop')
        else:
            repo.git.checkout('master')
        origin = repo.remote(name='origin')
        origin.pull()
        elapsed = time.time() - t0
        order_no = repo_names.index(repo_name) + 1
        msg = '[{}/{}] '+ color.BOLD +'{}'+ color.END +' repo updated in {:.2f} s'
        print(msg.format(order_no, repo_count, repo_name, elapsed))

def package_update():
    """Install gems and npm modules"""
    print(color.GREEN + "Updating gems" + color.END)
    os.chdir(fm_dir)
    subprocess.run('bundle update', shell=True, check=True)
    print("OK")
    print(color.GREEN + "Updating npm modules" + color.END)
    subprocess.run('npm update', shell=True, check=True)
    print("OK")

def db_actions():
    """Run db:migrate and db:seed"""
    os.chdir(fm_dir)
    print(color.GREEN + "Running db:migrate" + color.END)
    subprocess.run('bundle exec rake db:migrate', shell=True, check=True)
    print("OK")
    print(color.GREEN + "Running db:seed" + color.END)
    subprocess.run('bundle exec rake db:seed', shell=True, check=True)
    print("OK")

def start_app():
    """Start webpack and foreman server"""
    os.chdir(fm_dir)
    print(color.GREEN + "Starting foreman" + color.END)
    subprocess.run('foreman start', shell=True)

def revisit_process():
    start_db()
    update_repos()
    package_update()
    db_actions()
    start_app()

if __name__ == "__main__":
    if args.repos:
        update_repos()
    else:
        revisit_process()
