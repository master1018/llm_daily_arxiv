import utils
import query
import pytz
import time
import datetime
import argparse
from apscheduler.schedulers.blocking import BlockingScheduler

CN_TZ = pytz.timezone('Asia/Shanghai')

    
def cal_tz_diff():
    time_zone1 = pytz.utc
    time_zone2 = pytz.timezone('Asia/Shanghai')

    time1 = datetime.datetime(2023, 10, 25, 12, 0, tzinfo=time_zone1)
    time2 = datetime.datetime(2023, 10, 25, 12, 0, tzinfo=time_zone2)

    # 计算时间差
    time_difference = time1 - time2
    return time_difference.total_seconds()
    # 获取差值的秒数
    #seconds_difference = time_difference.total_seconds()

def init():
    parser = argparse.ArgumentParser(description='parameters for weekly dp')
    parser.add_argument('--config', type=str,
                        default="./config/basic.json")

    args = parser.parse_args()
    config_path = args.config

    config = utils.get_config(config_path)

    return config

def apschedule_job(job_id):
        t = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        print("tast start: ", t)
        config = init()

             # get dblp papers every monday
        today = datetime.datetime.today()
       
        query.query_weekly_paper(config)


def auto_task_apschedule():
    try:
        scheduler = BlockingScheduler()
        scheduler.add_job(apschedule_job, 'cron', hour='23', minute='30', args=['job'])
        scheduler.start()
    except KeyboardInterrupt:
        print('Stopped by Keyboard. Bye!')


if __name__ == '__main__':
   print("[START]")
   auto_task_apschedule()
   #apschedule_job(1)
   print("[END]")