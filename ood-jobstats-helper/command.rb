require 'open3'

class Command
  def to_s(jobid, cluster)
    "/usr/bin/sacct -P -n -X -o start,end,jobid,jobidraw -M %s -j %s" % [cluster, jobid]
  end

  AppProcess = Struct.new(:user, :pid, :pct_cpu, :pct_mem, :vsz, :rss, :tty, :stat, :start, :time, :command)

  # Parse a string output from the `ps aux` command and return an array of
  # AppProcess objects, one per process
  def parse(output)
    lines = output.strip.split("\n")
    lines.map do |line|
      AppProcess.new(*(line.split(" ", 11)))
    end
  end

  # Execute the command, and parse the output, returning and array of
  # AppProcesses and nil for the error string.
  #
  # returns [Array<Array<AppProcess>, String] i.e.[processes, error]
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
