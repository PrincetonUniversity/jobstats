This is a helper app that looks up start and end times for a job and generates a
Grafana URL with those times (and jobid), for easier job visualization.

## Install

For OnDemand 1.8 or later, the gemset provided with OnDemand is sufficient to run this app.

For OnDemand 1.7 or earlier, first run these commands after loading the OnDemand scl:

    bin/bundle install --path vendor/bundle

This will create a `Gemfile.lock`, a `.bundle/config` and `vendor/bundle` directory with dependencies.
All three ensure that Passenger starts this app with the dependencies installed to `vendor/bundle`.

## Configuration

The app expects Open Ondemand to be configured with a Grafana server and it will use that URL
when generating the URL. Panels from Jobstats Grafana dashboard should/can be used
in OnDemand's job listing.
