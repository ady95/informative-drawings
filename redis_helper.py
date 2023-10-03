import json
import time
from datetime import datetime
import io
import os
import redis

class RedisHelper():

    
    def __init__(self, settings):
        self.r = redis.StrictRedis(host=settings.Redis.HOST, port=settings.Redis.PORT, 
                                db=settings.Redis.DB, password=settings.Redis.PASSWORD,
                                decode_responses=True)


    # 주어진 key로 시작되는 값의 리스트을 리턴함
    def hscan(self, map_name, key = ""):
        result_list = []

        keys = self.r.hkeys(map_name)
        if key == "": return keys

        for k in keys:
            if k.startswith(key):
                result_list.append(k)

        return result_list


    def add(self, key, value):
        if type(value) != str:
                value = json.dumps(value, ensure_ascii=False)
        self.r.rpush(key, value)

    def list(self, key, start_index = 0, end_index = -1):
        return self.r.lrange(key, start_index, end_index)        


    #def get(self, map_name, key = None):
    def get(self, *args):
        if len(args) == 2:
            map_name = args[0]
            key = args[1]
            value = self.r.hget(map_name, key)
        else:
            key = args[0]
            value = self.r.get(key)

        return value

    # get -> json.loads
    def get_json(self, *args):
        value_json = self.get(*args)
        if value_json:
            value_json = json.loads(value_json)
        return value_json

    # 해당 map_name의 전체 dictionary를 리턴
    def get_all(self, map_name):
        dict_value = self.r.hgetall(map_name)
        return dict_value

    # get_all 중에 key, name에 해당하는 dict 값을 리턴
    def get_target_dict(self, map_name, target_key, target_value):
        all_dict = self.get_all(map_name)
        for _, dict_value in all_dict.items():
            dict_value = json.loads(dict_value)
            if dict_value.get(target_key) == target_value:
                return dict_value

        return None

    # 해당 map에 대해 value값을 주면 key값을 리턴함
    def rget(self, map_name, value):
        result = self.r.hgetall(map_name)
        for k, v in result.items():
            if type(k) == bytes: k = k.decode()
            if type(v) == bytes: v = v.decode()

            if v == value:
                return k
        return None


    #def set(self, map_name, map):
    def set(self, *args):
        if len(args) == 3:        #hset
            map_name = args[0]
            key = args[1]
            value = args[2]
            if type(value) != str:
                value = json.dumps(value, ensure_ascii=False)
            self.r.hset(map_name, key, value)
        elif type(args[1]) == dict: #hmset
            map_name = args[0]
            map = args[1]
            self.r.hmset(map_name, map)
        else:                       #set
            key = args[0]
            value = args[1]
            if type(value) != str:
                value = json.dumps(value, ensure_ascii=False)
            self.r.set(key, value)
        
    def delete(self, *args):
        if len(args) == 2:        #hdel
            map_name = args[0]
            key = args[1]
            self.r.hdel(map_name, key)
        else:                     #delete
            key = args[0]
            self.r.delete(key)   


    # json value에서 특정키에 대한 값을 가져옴
    def get_dict_value(self, redis_key, key, dict_key, default_value = None):
        dict_value = self.get(redis_key, key)
        if dict_value:
            print(dict_value)
            dict_value = json.loads(dict_value)
            value = dict_value.get(dict_key, None)
            if value:
                return value

        return default_value


    def set_dict_value(self, redis_key, key, dict_key, value):
        dict_value = self.get(redis_key, key)
        if dict_value:
            dict_value = json.loads(dict_value)
        else:
            dict_value = {}
        dict_value[dict_key] = value
        self.set(redis_key, key, json.dumps(dict_value, ensure_ascii=False))

    def del_dict_value(self, redis_key, key, dict_key):
        dict_value = self.get(redis_key, key)
        if dict_value:
            dict_value = json.loads(dict_value)
        else:
            dict_value = {}
        del dict_value[dict_key]
        self.set(redis_key, key, json.dumps(dict_value, ensure_ascii=False))

    def get_config(self, config_key, json_value = False, default_value = None, config_type = "talk"):
        key = self.HEUMTALK_CONFIG
        if config_type == "noti":
            key = self.NOTI_CONFIG

        value = self.get(key, config_key)
        if json_value and value != None:
            value = json.loads(value)

        if value == None:
            return default_value
        else:
            return value

    def set_config(self, config_key, value, json_value = False, config_type = "talk"):
        key = self.HEUMTALK_CONFIG
        if config_type == "noti":
            key = self.NOTI_CONFIG
            
        if json_value:
            value = json.dumps(value, ensure_ascii = False)
        self.set(key, config_key, value)

  
    # redis 백업
    def backup(self, folder_path = r"D:\NEIL\REDIS_백업"):
        timestamp = datetime.now().strftime("%Y%m%d")
        backup_folder = os.path.join(folder_path, timestamp)
        print(backup_folder)
        if not os.path.exists(backup_folder):
            os.makedirs(backup_folder)


        target_list = self.r.scan_iter("*")
        
        for target in target_list:
            print(target, self.r.type(target))
            
            if self.r.type(target) == "hash":
                result = self.r.hgetall(target)
                json_obj = {}
                for k, v in result.items():
                    # k = k.decode()
                    # v = v.decode()
                    json_obj[k] = v
            else:
                # type이 hash가 아닌 key는 skip함
                continue

            target = target.replace(":", "_")   # 파일명을 위해 ":"->"_"로 변경
            json_path = os.path.join(backup_folder, target + ".json")

            with io.open(json_path, 'w', encoding='utf-8') as outfile:
                outfile.write(json.dumps(json_obj, indent=3, ensure_ascii=False))

    # 백업한 json 파일로부터 restore
    def restore(self):
        backup_file = r"D:\NEIL\REDIS_백업\2017-12-19\heumdesk_member.json"
        REDIS_HEUMDESK_REGISTER_BUSINESS = "heumdesk:register_business"
        json_string = common_util.read_text(backup_file)
        member_dict = json.loads(json_string)
        for id, line in member_dict.items():
            company_dict = json.loads(line)
            if "이창근" != company_dict["user_name"]:
                print(id, line)
                self.set(REDIS_HEUMDESK_REGISTER_BUSINESS, id, line)


    # redis 일괄 값 등록
    def put_values(self):
        json_text = common_util.read_text(r"D:\GIT\neil_work\slack_tool\test\heum_token.txt")
        token_list = json.loads(json_text)
        for item in token_list:
            name = item["name"]
            token = item["token"]
            print(name, token)
            self.set(self.REDIS_SLACK_TOKEN, name, token)



    def test(self):
        #result = self.get(self.REDIS_SLACK_TOOL_MAIL_TO_SLACK)
        #result = self.r.hgetall(self.REDIS_SLACK_TOOL_MAIL_TO_SLACK)
        result = '{"rosa@rosaent.com": "C4XGFF50C", "ksm7137@naver.com": "C4XGFERNY", "han@seyeonpat.com": "C4YNJ3AF9", "salermkt@naver.com": "C4Y6AF13Q", "yongwook@onlharu.com": "C4XFA3QAE", "jeongho.shin@gmail.com": "C4Y5Y964W", "jacquelynceo@jacquelyn.co.kr": "C4XJAR5EZ", "soohan-lim@hanmail.net": "C4XFA723C", "hs.kim@design-paprika.com": "C4Y6ADWSJ", "adyz95@gmail.com": "C4Y6ANQ1L", "ady95@nextlab.co.kr": "C4ZAD1TT9", "admin@divememory.com": "C4WPZ3E72", "yumi@divememory.com": "C4WQB6YSU", "djj7856@hanmail.net": "C4Y68HNK1", "w_rent@daum.net": "C4XFA4RGA", "ceo@lacuisine.co.kr": "C4XFNA9R8", "account@lacuisine.co.kr": "C4WQT4H25", "marc@malang.kr": "C4Y6AEJ5C", "help@madeinreal.com": "C4WPZ2T6C", "cwpark00@hotmail.com": "C4Y5Y92S2", "supia_eco@naver.com": "C4XHYPFQV", "candyflip@naver.com": "C4WR56H89", "david@sparkplus.co": "C4WQT2E3T", "srkim@idw.kr": "C4WPZ23JL", "wonders21@idcane.co.kr": "C4WR57KS5", "afocus@naver.com": "C4Y6AELKG", "geun7978@naver.com": "C4Y6LMP3R", "kbeen@adxcorp.kr": "C4XJB47RT", "james@mpeco.co.kr": "C4Y6AE9L6", "helen@mpeco.co.kr": "C4WQB7E5N", "bkyoung311@gmail.com": "C4WQT1VPB", "zellta@nate.com": "C4XDAK403", "drkim.ost@gmail.com": "C4XFN958A", "osteonateurecentre@gmail.com": "C4Y6AEUKY", "lee@cardanoplus.com": "C4XDNS275", "parkig4430@naver.com": "C4WPZ2PUY", "dave@classting.com": "C4XFA5682", "minji@classting.com": "C4XJAR86R", "heejong.jin@taggers.io": "C4XFN9TD0", "fairway911@techtreespace.com": "C4XHYMESZ", "inno@trnti.com": "C4WPZ37S4", "journal_1987@naver.com": "C4XJASPAR", "minhoshin@molik.kr": "C53R1S03Y", "yulduck.sung@genu.io": "C532SG7MJ", "hyewonrho@debateforall.org": "C4XJB466R", "max@sparkplus.co": "C4XDAKKA7", "surreal1098@naver.com": "C4XGTT8VA", "suji@classting.com": "C4XJAR86R"}'
        result = json.loads(result)
        print(type(result))
        print(result["ksm7137@naver.com"])
        self.r.hmset(self.REDIS_SLACK_TOOL_MAIL_TO_SLACK_1, result)


if __name__ == "__main__":
    # import common_util
    import time
    import config as settings

    redisHelper = RedisHelper(settings)
    # print(redisHelper.r.getrange(0, 2))
    # exit()
    # for i in range(10):
    #     timestamp = common_util.get_timestamp()

    #     dict_value = {
    #         "timetamp": timestamp
    #     }
    #     ret = redisHelper.add("timetamp", dict_value)
    #     print(ret)
    #     time.sleep(1)

    # ret = redisHelper.list("timetamp", start_index = -3)
    # print(ret)

    ret = redisHelper.get_all("01090014461")
    print(ret)
    print(len(ret))

    exit()
    redisHelper.set("01090014461", "photo", "https://files.slack.com/files-pri/T05TH4T3WMD-F05TS025GHM/download/_______crop.jpg")
    redisHelper.set("01090014461", "anime", "https://files.slack.com/files-pri/T05TH4T3WMD-F05TS025GHM/download/_______crop.jpg")
    redisHelper.set("01090014461", "drawing", "https://files.slack.com/files-pri/T05TH4T3WMD-F05TS025GHM/download/_______crop.jpg")
    redisHelper.set("01090014461", "svg", "https://files.slack.com/files-pri/T05TH4T3WMD-F05TS025GHM/download/_______crop.jpg")


