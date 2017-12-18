#!/usr/bin/env python

from collections import defaultdict
import codecs
import json
import os
import pystache
import requests
import time
import netrc
from pygithub3 import Github
from git import Repo

import warnings
import requests
import contextlib
import sys
import operator

##voodooo to turn of SSL security (our ghe has self signed certificates
try:
    from functools import partialmethod
except ImportError:
    # Python 2 fallback: https://gist.github.com/carymrobbins/8940382
    from functools import partial

    class partialmethod(partial):
        def __get__(self, instance, owner):
            if instance is None:
                return self

            return partial(self.func, instance, *(self.args or ()), **(self.keywords or {}))

@contextlib.contextmanager
def no_ssl_verification():
    old_request = requests.Session.request
    requests.Session.request = partialmethod(old_request, verify=False)

    warnings.filterwarnings('ignore', 'Unverified HTTPS request')
    yield
    warnings.resetwarnings()

    requests.Session.request = old_request

repos_in = 'repos.json'
index_in = 'index.mustache'
index_out = 'index.html'

#get the repo name from origin
repo = Repo('.')
assert not repo.bare
url = repo.remotes.origin.url
(url2, _, name) = url.rpartition('/')
(tld, _, owner) = url2.rpartition('/')
(proto, _, domain) = tld.rpartition('/')

# so GitHubEnterprose (GHE) API is at github.your.domain/api/v3
# whereas github.com is at api.github.com
print(repo.remotes.origin.url)

if domain == 'github.com':
    api = proto + '/api.github.com/'
else:
    api = tld + '/api/v3/'

try:
  #are we running in CI so use the credentials
  inCI = False
  if inCI:
      pass
  else:
    auth = netrc.netrc()
    (login, _, password) = auth.authenticators(domain)

  ghclient = Github(login=login, password=password, base_url=api)
  logged_in = True
except:
  print "Unexpected error:", sys.exc_info()[0]
  ghclient = Github(base_url=api)
  logged_in = False

def gh_repo(name):
  print('Fetching "%s%s/%s" repo information...' % (api, owner, name) )
  # Use the following for development so you do not hammer the GitHub API.
  #return {'name': name, 'html_url': 'http://google.com', 'homepage': 'http://example.com', 'description': 'Description!'}

  if not logged_in:
    time.sleep(2.0) # Take a nap so GitHub doesn't aggressively throttle us.

  with no_ssl_verification():
    repo = ghclient.repos.get(user=owner, repo=name )
    return dict(
      name=repo.name,
      homepage=repo.homepage,
      html_url=repo.html_url,
      description=repo.description
    )

with no_ssl_verification():
  temp = filter(lambda y: y.owner.login == owner, ghclient.repos.list(owner).all())
  repos = map(lambda x: x.html_url.rpartition('/')[2], temp)

# Multimap of categories to their repos.
categories = defaultdict(list)

# Loop through declared repos, looking up their info on GitHub and adding to the specified categories.
for repo in repos:
  with no_ssl_verification():
    langs =   ghclient.repos.list_languages(user=owner, repo=repo)

  if any(langs):
    repo_cats = [ max(langs.iteritems(), key=operator.itemgetter(1))[0] ]
  else:
    repo_cats = ['Other']

  repo_data = gh_repo(repo)

  for repo_cat in repo_cats:
    categories[repo_cat].append(repo_data)

# Template context that will be used for rendering.
context = {
  'categories': []
}

# Loop over the category names sorted alphabetically (case-insensitive) with 'Other' last.
for category_name in sorted(categories.keys(), key=lambda s: s.lower() if s is not 'Other' else 'z'*10):
  data = {
    'name': category_name,
    'index': category_name.lower(),
    'has_repos_with_images': False,
    'has_repos_without_images': False,
    'repos_with_images': [],
    'repos_without_images': [],
  }

  # Loop over category repos sorted alphabetically (case-insensitive).
  for repo_data in sorted(categories[category_name], key=lambda s: s['name'].lower()):
    name = repo_data['name']
    repo = {
      'name': name,
      'href': repo_data['html_url'],
      'website': repo_data.get('homepage', None),
      'description': repo_data.get('description', None)
    }
    if os.path.exists(os.path.join('repo_images', '%s.jpg' % name)):
      data['repos_with_images'].append(repo)
      data['has_repos_with_images'] = True
    else:
      data['repos_without_images'].append(repo)
      data['has_repos_without_images'] = True

  context['categories'].append(data)

# Render the page HTML using MOOOUUSSTTAACCCCHHEEEEE!
renderer = pystache.Renderer()
with codecs.open(index_in, 'r', 'utf-8') as f:
  template = pystache.parse(f.read())
html = renderer.render(template, context)

with codecs.open(index_out, 'w', 'utf-8') as f:
  f.write(html)

# Rejoice. If you got this far, it worked!
