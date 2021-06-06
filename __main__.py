import requests
from io import BytesIO
import zipfile
import xmltodict
import json
from config import cnfg
import matplotlib.pyplot as plt

# API key
API_KEY = cnfg['apiKey']

# 회사 리스트 불러오기
URL_ALL_CORP = 'https://opendart.fss.or.kr/api/corpCode.xml'
ALL_CORP_PARAM = {
    'crtfc_key': API_KEY
}
resCorpList = requests.get(URL_ALL_CORP, params=ALL_CORP_PARAM)

# xml data → dict data → list data
data_xml = zipfile.ZipFile(BytesIO(resCorpList.content))
data_xml = data_xml.read('CORPCODE.xml').decode('utf-8')
data_odict = xmltodict.parse(data_xml)
data_dict = json.loads(json.dumps(data_odict))
data = data_dict.get('result', {}).get('list')

# 검색한 회사의 회사코드 추출
myCorpName = input("회사명을 입력하세요. : ")
myCorpCode = None
for item in data:
    if item['corp_name'] == myCorpName:
        myCorpCode = item['corp_code']

print("회사코드 : {0}".format(myCorpCode))
myCorpYear = input("보고자 하는 년도를 입력하세요.(2020 입력시 2018 ~ 2020 출력): ")

# 검색한 회사의 2018 ~ 2020 사업보고서 불러오기
URL_MY_CORP = 'https://opendart.fss.or.kr/api/fnlttSinglAcnt.json'
MY_CORP_PARAMS = {
    'crtfc_key': API_KEY,
    'corp_code': myCorpCode,  # 삼성전자 고유번호
    'bsns_year': myCorpYear,  # 사업연도(4자리)
    'reprt_code': '11011',  # 사업보고서
}
resMyCorp = requests.get(url=URL_MY_CORP, params=MY_CORP_PARAMS)

# http 정상응답시 처리
TA = None # 자산총계 (Total Assets)
TB = None # 부채총계 (Total Dept)
DR = [] # 부채비율 (Debt Ratio)
SR = None # 매출액 (Sales Revenue)
NPDT = None # 당기순이익 (Net Profit During the Term)

if resMyCorp.status_code == 200:
    corpDataJson = resMyCorp.json()

    # output
    # corpDataStr = json.dumps(corpDataJson, indent=4, ensure_ascii=False)
    # print(corpDataStr) # 전체 회사 리스트
    if corpDataJson['status'] == "000":
        detail = corpDataJson['list']
        for item in detail: #자산총계
            if item['fs_div'] == 'CFS' and item['sj_div'] == 'BS' and item['account_nm'] == '자산총계':
                TA = item
        for item in detail: #부채총계
            if item['fs_div'] == 'CFS' and item['sj_div'] == 'BS' and item['account_nm'] == '부채총계':
                TB = item
        for item in detail: #매출액 정리
            if item['fs_div'] == 'CFS' and item['sj_div'] == 'IS' and item['account_nm'] == '당기순이익':
                SR = item
        for item in detail: #당기순이익 정리
            if item['fs_div'] == 'CFS' and item['sj_div'] == 'IS' and item['account_nm'] == '매출액':
                NPDT = item
    else:
        print(corpDataJson['message'])

# 부채비율 계산 { 부채비율 = (부채총계 / 자산총계) * 100 }
TA_1 = int(TA['bfefrmtrm_amount'].replace(",", "")) # (ex = 2018)
TB_1 = int(TB['bfefrmtrm_amount'].replace(",", ""))
TA_2 = int(TA['frmtrm_amount'].replace(",", "")) # (ex = 2019)
TB_2 = int(TB['frmtrm_amount'].replace(",", ""))
TA_3 = int(TA['thstrm_amount'].replace(",", "")) # 가장 최근년도 (ex = 2020)
TB_3 = int(TB['thstrm_amount'].replace(",", ""))

# 부채비율 리스트 삽입
def calcDeptRatio(ta, tb):
    dr = round((ta / tb) * 100, 2)
    return dr

DR.append(calcDeptRatio(TB_1, TA_1))
DR.append(calcDeptRatio(TB_2, TA_2))
DR.append(calcDeptRatio(TB_3, TA_3))

# 재무 출력
print("==={0} {1} ~ {2} 정보===\n".format(myCorpName, str(int(myCorpYear)-2), myCorpYear))
print(" - 자산총계 -")
print("{0} : {1} (원)".format(TA['bfefrmtrm_dt'], TA['bfefrmtrm_amount']))
print("{0} : {1} (원)".format(TA['frmtrm_dt'], TA['frmtrm_amount']))
print("{0} : {1} (원)\n".format(TA['thstrm_dt'], TA['thstrm_amount']))
print(" - 부채비율 -")
print("{0} : {1} (%)".format(SR['bfefrmtrm_dt'], DR[0]))
print("{0} : {1} (%)".format(SR['frmtrm_dt'], DR[1]))
print("{0} : {1} (%)\n".format(SR['thstrm_dt'], DR[2]))
print(" - 매출액 -")
print("{0} : {1} (원)".format(SR['bfefrmtrm_dt'], SR['bfefrmtrm_amount']))
print("{0} : {1} (원)".format(SR['frmtrm_dt'], SR['frmtrm_amount']))
print("{0} : {1} (원)\n".format(SR['thstrm_dt'], SR['thstrm_amount']))
print(" - 당기순이익 -")
print("{0} : {1} (원)".format(NPDT['bfefrmtrm_dt'], NPDT['bfefrmtrm_amount']))
print("{0} : {1} (원)".format(NPDT['frmtrm_dt'], NPDT['frmtrm_amount']))
print("{0} : {1} (원)\n".format(NPDT['thstrm_dt'], NPDT['thstrm_amount']))
