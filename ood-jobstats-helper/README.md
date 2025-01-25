## OOD Jobstats Helper

A helper OOD app that given jobid provides a link to Grafana dashboard with
details for that job.

## Prerequisites
Grafana with a compatible dashboard and OnDemand configured to use that dashboard, e.g. check
[OnDemand Grafana documentation](https://osc.github.io/ood-documentation/latest/customizations.html#grafana-support)

## Install

For OnDemand 3.1 or later just drop in /var/www/ood/apps/sys and remove Gemfile and Gemfile.lock.

For older versions and/or versions running on RHEL7 you may have to generate gem bundle. E.g. for RHEL7:
    scl enable rh-ruby30 bash
    cd /var/www/ood/apps/sys/ood-jobstats-helper
    rm -rf vendor/bundle Gemfile.lock
    gem install bundler -v 2.2.22
    scl enable rh-ruby30 -- bundle install

This will create a Gemfile.lock, a .bundle/config and vendor/bundle directory with dependencies.
All three ensure that Passenger starts this app with the dependencies installed to vendor/bundle.
