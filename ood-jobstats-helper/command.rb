require 'open3'

class Command
  def to_s(jobid, cluster)
    "/usr/bin/sacct -P -n -X -o start,end,jobid,jobidraw -M %s -j %s" % [cluster, jobid]
  end

  def exec(jobid, cluster)
    processes, error = nil, nil
    
    stdout_str, stderr_str, status = Open3.capture3({'SLURM_TIME_FORMAT'=>'%s'},to_s(jobid, cluster))

    if status.success?
      #processes = parse(stdout_str)
      processes = stdout_str
    else
      error = "Querying jobid #{jobid} for cluster #{cluster} exited with error: #{stderr_str}"
    end

    [processes, error]
  end
end
