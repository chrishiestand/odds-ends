#!/opt/local/bin/python3.2
#Requires python3
#TODO use a multithread or multiprocess module to speed up processing
import os, sys, argparse, re
from operator import itemgetter
from datetime import datetime, date, time, timedelta, tzinfo

class ApacheLogLine:
  
  maxLengths = {'date_time' : 9, 'seconds' : 7, 'bytes' : 5, 'rate': 3,'status' : 6} #these numbers are lengths of hard-coded column headers, used for column padding

  def __init__(self, RequestData):
    if RequestData['bytes'] == '-':
      RequestData['bytes'] = '0'
    for digits in ['status', 'bytes', 'seconds', 'microseconds']:
      if not RequestData[digits].isdigit():
        raise AttributeError('Could not determine bytes for requestData: ' + str(RequestData))

    self.remote_host   = RequestData['remote_host']
    self.log_name      = RequestData['log_name']
    self.user_name     = RequestData['user_name']
    self.date_time     = datetime.strptime(RequestData['date_time'], "%d/%b/%Y:%H:%M:%S %z") #%z requires python3.2 *grumbles*, also silently truncates timezone - see timetuple()
    self.date_time     = self.date_time.replace(tzinfo=None)  #even though the timezone isn't set, you have to force it back to naive mode
    self.request_line1 = RequestData['request_line1']
    self.status        = int(RequestData['status'])
    self.bytes         = int(RequestData['bytes'])
    self.seconds       = int(RequestData['seconds'])
    self.microseconds  = int(RequestData['microseconds'])
    self.rate          = int(self.bytes / self.microseconds * 1000000)


  def print(self):
    print(self.date_time.strftime("%Y-%m-%d:%H:%M:%S").ljust(ApacheLogLine.maxLengths['date_time']), ' ', str(self.seconds).rjust(ApacheLogLine.maxLengths['seconds']) , ' ' , str(self.bytes).rjust(ApacheLogLine.maxLengths['bytes']), ' ', str(self.rate).rjust(ApacheLogLine.maxLengths['rate']) , ' ', str(self.status).rjust(ApacheLogLine.maxLengths['status']), ' ', self.request_line1)


  def isDuring(self, targetTime):
    targetTime = datetime.strptime(targetTime, "%Y-%m-%d:%H:%M:%S")
    endTime = self.date_time + timedelta(seconds = self.seconds)
    
    if targetTime >= self.date_time and targetTime <= endTime:
      return True
    return False

parser = argparse.ArgumentParser(description= "Scan customized apache log files to find requests with slow responses and/or all downloads at a given time.")

defaultResponsetime = 0
defaultSort = 'date_time'

parser.add_argument("-m", "--minimum-seconds", dest="minimumResponseTime", type=int, default=defaultResponsetime, help="Show responses which have taken at minimum t seconds. default: " + str(defaultResponsetime))
parser.add_argument('logs', metavar='logfile', type=str, nargs='+', help='apache logfile with format: "%%h %%l %%u %%t \\"%%r\\" %%>s %%b %%T %%D \\"%%{Referer}i\\" \\"%%{User-Agent}i\\""')
parser.add_argument("-s", "--sort", dest="sort", type=str, default=defaultSort, choices = ['date_time', 'seconds', 'bytes'], help="Which field to sort results by, default: " + defaultSort)
parser.add_argument("-t", "--at-time", dest="targetTime", type=str, help="Show active connections during at time in form: yyyy-mm-dd:HH:MM:SS")

args = parser.parse_args()
lines = []

for logfile in args.logs:
  try:
    logfilehandle = open(logfile, 'r')
  except IOError as e:
    print("I/O error({0}), {1}: {2}".format(e.errno, e.strerror, logfile))
    sys.exit(2)


  for line in logfilehandle:
      
    try:
      matches = re.match("(?P<remote_host>\S+) (?P<log_name>\S+) (?P<user_name>\S+) \[(?P<date_time>[^\]]+)\] \"(?P<request_line1>.+)\" (?P<status>\d+) (?P<bytes>\S+) (?P<seconds>\d+) (?P<microseconds>\d+) .*" , line.strip()).groupdict()
    except AttributeError: #skip non-matching lines
      print("Skipping non-conforming line: " + line)
      continue
      
    if matches and int(matches['seconds']) >= args.minimumResponseTime:
      try:
        ALL = ApacheLogLine(matches)
        
      except AttributeError:
        print("Could not parse line:\n" + line)
        raise
        sys.exit(3)

    if args.targetTime:
      if ALL.isDuring(args.targetTime):
        lines.append(ALL)
      else:
        continue
    else:
      lines.append(ALL)

    ApacheLogLine.maxLengths['date_time'] = max(ApacheLogLine.maxLengths['date_time'], len(str(ALL.date_time)))
    ApacheLogLine.maxLengths['seconds']   = max(ApacheLogLine.maxLengths['seconds'], len(str(ALL.seconds)))
    ApacheLogLine.maxLengths['bytes']     = max(ApacheLogLine.maxLengths['bytes'], len(str(ALL.bytes)))
    ApacheLogLine.maxLengths['rate']     = max(ApacheLogLine.maxLengths['rate'], len(str(ALL.rate)))
    ApacheLogLine.maxLengths['status']    = max(ApacheLogLine.maxLengths['status'], len(str(ALL.status)))


if args.sort == 'date_time':
  lines = sorted(lines, key=lambda logline: logline.date_time)
elif args.sort == 'bytes':
  lines = sorted(lines, key=lambda logline: logline.bytes)
elif args.sort == 'seconds':
  lines = sorted(lines, key=lambda logline: logline.seconds)  

print("Date-Time".ljust(ApacheLogLine.maxLengths['date_time']), ' ',   'Seconds'.rjust(ApacheLogLine.maxLengths['seconds']), ' ', 'Bytes'.rjust(ApacheLogLine.maxLengths['bytes']) , ' ', 'B/S'.rjust(ApacheLogLine.maxLengths['rate']) ,' ', 'Status'.rjust(ApacheLogLine.maxLengths['status']), ' ' ,  'Reuqest-Line-1')
for line in lines:
  line.print()