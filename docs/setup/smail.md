# smail

The jobstats command is also used to replace smail, which is the Slurm executable used for sending email reports that are based on seff. This means that users receive emails that are the exact output of jobstats including the notes.

To generate email reports using jobstats after a job finishes, the following line is needed in slurm.conf: MailProg=/usr/local/bin/jobstats_mail.sh Here are the key lines in the jobstats_mail.sh script: SEFF=/usr/local/bin/jobstats--no-color $SEFF $jobid | $MAIL-s "$subject" $recipient

One also needs to set the content-type to text/html so that the email uses a fixed-width font. The full script is available in the Jobstats GitHub repository [18].
