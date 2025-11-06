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
    "#{host}/d/#{dashid}/ondemand-clusters/?orgId=#{orgid}&theme=#{theme}&kiosk"
  end

  def stat_urls(jobid, cluster)
    check_jobid(jobid)
    @command = Command.new
    data = Hash.new
    @details, @err = @command.exec(jobid, cluster)
    if @err
      raise StandardError.new("ERROR: " + @err)
    else
      url = grafana_url(cluster)
      @details.strip.split(' ') do |line|
        sd = line.strip.split('|')
        if sd.size != 4
          raise StandardError.new("ERROR: Invalid sacct output " + @details)
        else
          sd[0] += "000"
          if sd[1] == 'Unknown'
            sd[1] = "now"
           else
            sd[1] += "000"
          end
          staturl = "%s&from=%s&to=%s&var-JobID=%s" % [url, sd[0], sd[1], sd[3]]
          desc = "<td>%s</td><td>%s</td>" % [sd[2], sd[3]]
          data[desc] = staturl
        end
      end
    end
    data
  end

  def stat_html(stats)
    data = '<table class="table"><thead><tr class="thead-light"><th scope="row">Job ID</th><th>Raw Job ID</th><th>Link with detailed statistics</th></tr></thead><tbody>'
    stats.each do |desc, staturl|
      data += '<tr>%s<td><a href="%s" target="_blank">Click here for stats</a></td></tr>' % [desc,staturl]
    end
    data += '</tbody></table>'
  end

  def check_jobid(jobid)
    if /^[0-9]+([\.\+_][0-9]+)?$/ !~ jobid
      raise StandardError.new("ERROR: Invalid jobid #{jobid}")
    end
  end
end

OODClusters = OodCore::Clusters.new(OodAppkit.clusters.select(&:allow?).reject { |c| c.job_config[:adapter] != "slurm" })
default_cluster = OODClusters.count == 1 ? OODClusters.first.id : nil

# Define a route at the root '/' of the app.
# with optional params for jobid and cluster
# either /4441111 (in case of a single cluster) or /clustername/444111
get '/:first?/?:second?' do
  @jobdetails = ""
  @joberror = ""
  jobid = nil
  cluster = nil
  begin
    if not params[:first].blank?
      if params[:second].blank?
        if default_cluster.blank?
          raise StandardError.new("No cluster name given with more than one cluster available on this OOD instance.")
        end
        jobid = params[:first]
        cluster = default_cluster
      else
        cluster = params[:first]
        jobid = params[:second]
      end
      if OODClusters[cluster].nil?
        raise StandardError.new("No such cluster: #{cluster}")
      end
      stats = stat_urls(jobid, cluster)
      if stats.size > 1
        @jobdetails = stat_html(stats)
      else
        redirect to(stats.values[0])
      end
    end
  rescue StandardError => e
    @joberror = e.message
  end
  # Render the view
  erb :index
end

post '/' do

  jobid = params[:jobid]
  cluster = params[:cluster]
  url = grafana_url(cluster)
  if jobid
    if request.xhr?
      begin
        stat_html(stat_urls(jobid, cluster))
      rescue StandardError => e
        e.message
      end
    end
  end
end
