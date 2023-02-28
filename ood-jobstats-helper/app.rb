require 'erubi'
require 'rails/all'
require 'ood_core'
require 'ood_appkit'
require './command'

set :erb, :escape_html => true

if development?
  require 'sinatra/reloader'
  also_reload './command.rb'
end

helpers do
  def dashboard_title
    ENV['OOD_DASHBOARD_TITLE'] || "Open OnDemand"
  end

  def dashboard_url
    "/pun/sys/dashboard/"
  end

  def title
    "Job Stats Helper"
  end

  def grafana_url(cluster)
    c = OODClusters[cluster]
    server = c.custom_config(:grafana)
    host = server[:host]
    orgid = server[:orgId]
    dashid = server[:dashboard]['uid']
    theme = server[:theme] || 'light'
    "#{host}/d/#{dashid}/ondemand-clusters/?orgId=#{orgid}&theme=#{theme}"
  end
end

OODClusters = OodCore::Clusters.new(OodAppkit.clusters.select(&:allow?))

# Define a route at the root '/' of the app.
get '/' do

  # Render the view
  erb :index
end

post '/' do
  @command = Command.new

  jobid = params[:jobid]
  cluster = params[:cluster]
  url = grafana_url(cluster)
  if jobid
    @details, @error = @command.exec(jobid, cluster)
    if request.xhr?
	if @error
	  "ERROR: " + @error
	else
          data = ""
	  @details.strip.split(' ') do |line|
	    sd = line.strip.split('|')
	    if sd.size != 4
              data = "ERROR: Invalid sacct output " + @details
	    else
              sd[0] += "000"
	      if sd[1] == 'Unknown'
	        sd[1] = "now"
	      else
                sd[1] += "000"
	      end
              staturl = "%s&from=%s&to=%s&var-JobID=%s" % [url, sd[0], sd[1], sd[3]]
	      if sd[2] != sd[3]
                desc = "array job %s, raw job id %s" % [sd[2], sd[3]]
	      else
		desc = "job id %s" % sd[3]
	      end
              data += '<p><a href="%s" target="_blank">Open webpage with stats for %s</a></p>' % [staturl, desc]
            end
	  end
	  data
	end
    else
      @details
    end
  end
end
