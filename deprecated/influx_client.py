from influxdb import InfluxDBClient
import time


class influx_client:
    def __init__(self, host, port, username, password, database):
        self.client = InfluxDBClient(host, port, username, password, database)
        self.obj = [
            {
                "measurement" : "test",
                "tags" : {
                    "testTag" : "asdasd"
                    },
                "time" : int(time.time() * 1000),
                "fields" : {
                    "testField" : 123
                    }
            }
        ]
        
#while True:
#    print(influx.obj[0])
#    influx.obj[0]["time"] = int(time.time() * 1000)
 #   influx.client.write_points(influx.obj, time_precision="ms", retention_policy="30d")
  #  print("Uploaded")
   # time.sleep(10)
