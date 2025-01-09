# ood-example-ps

Example Open OnDemand app that displays the output of `ps`


## Install

For OnDemand 1.8 or later, the gemset provided with OnDemand is sufficient to run this app.

For OnDemand 1.7 or earlier, first run these commands after loading the ondemand scl:

    bin/bundle install --path vendor/bundle

This will create a Gemfile.lock, a .bundle/config and vendor/bundle directory with dependencies.
All three ensure that Passenger starts this app with the dependencies installed to vendor/bundle.
