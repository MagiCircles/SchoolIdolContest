LoveLive! School Idol Contest
=============================

A Facemash-like web application based on the Love Live! franchise.

Cards data are fetched using [the unofficial School Idol API](https://github.com/db0company/SchoolIdolAPI).

Getting Started
---------------

```shell
# Clone the repo
git clone https://github.com/Engil/SchoolIdolContest.git
cd SchoolIdolContest

# Create a virtualenv to isolate the package dependencies locally
virtualenv env
source env/bin/activate

# Install dependencies & setup project
python setup.py develop
initialize_SchoolIdolContest_db development.ini

# Install client-side dependencies & compile CSS
npm install bower
bower install
mkdir -p schoolidolcontest/static/css/
lessc --compress schoolidolcontest/static/less/style.less > schoolidolcontest/static/css/style.css

# Launch server
pserve development.ini --reload
```

Screenshots
===========

Vote
-----

![School Idol Contest COCOisBEST](http://i.imgur.com/awingob.png)

Ranking
-------

![School Idol Contest COCOisBEST](http://i.imgur.com/Gzq2a8Y.png)
