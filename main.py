from tkinter import *
from tkinter import ttk
from ttkbootstrap import Style
import requests
from io import BytesIO
import zipfile
import xmltodict
import json
from config import cnfg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
#========================================================================================================
# 전역 변수=================================================================================================
myCorp = {'name': None, 'start_year': None, 'corp_code': None, 'stock_code': None}

TA = None  # 자산총계 (Total Assets)
TB = None  # 부채총계 (Total Dept)
DR = []  # 부채비율 (Debt Ratio)
SR = None  # 매출액 (Sales Revenue)
NPDT = None  # 당기순이익 (Net Profit During the Term)

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

# Function================================================================================================
def consoleLoging(textObject, start, print):
    textObject.configure(state='normal')
    textObject.insert(start, print)
    textObject.configure(state='disabled')

def resetForm():
    for i, label in enumerate([cont1_name_ent, cont1_start_year_ent, cont1_CC_ent, cont1_SC_ent]):
        label.configure(state='normal')
        label.delete(0, END)
    cont1_CC_ent.configure(state='disabled')
    cont1_SC_ent.configure(state='disabled')
    consoleLoging(cont2_text, END, "Data reset...\n")

def makeGragh(dict, string, canvasFrame, strXLabel, strYLabel, bgcolor):
    consoleLoging(cont2_text, END, "{0} Graph 작성...".format(string))

    start_year = int(myCorp['start_year'])

    dict['bfefrmtrm_amount'] = int(dict['bfefrmtrm_amount'].replace(',',''))
    dict['frmtrm_amount'] = int(dict['frmtrm_amount'].replace(',', ''))
    dict['thstrm_amount'] = int(dict['thstrm_amount'].replace(',', ''))

    x_data = [str(start_year - 2),str(start_year - 1), str(start_year)]
    y_data = [dict['bfefrmtrm_amount'], dict['frmtrm_amount'], dict['thstrm_amount']]

    fig = Figure(figsize=(7, 5), facecolor=bgcolor, dpi=60)  # 그래프 그릴 창 생성
    axis = fig.add_subplot(1, 1, 1)
    t = axis.plot(x_data, y_data)
    axis.set_xlabel(strXLabel)
    axis.set_ylabel(strYLabel)
    axis.grid()
    fig.legend(t, string)

    canvas = FigureCanvasTkAgg(fig, master=canvasFrame)
    canvas.draw()
    canvas.get_tk_widget().pack(side=BOTTOM, fill=BOTH)
    consoleLoging(cont2_text, END, "완료!\n")

def calcDeptRatio(ta, tb): # 부채비율 리스트 삽입
    dr = round((ta / tb) * 100, 2)
    return dr

def get_form_data(self):
    if self.name.get() != '':
        myCorp['name'] = self.name.get()
    else:
        consoleLoging(cont2_text, END, "회사명을 입력하세요.\n")
        return 0
    if self.start_year.get() != '':
        myCorp['start_year'] = self.start_year.get()
    else:
        consoleLoging(cont2_text, END, "년도를 입력하세요. (ex: 2020)\n")
        return 0

    consoleLoging(cont2_text, END, "Form data 전송\n")
    mainDo()

def mainDo():
    consoleLoging(cont2_text, END, "Main function 진입\n")
    consoleLoging(cont2_text, END, "{0} Data 검색중...\n".format(myCorp['name']))
    # myCorp data 입력
    for item in data:
        if item['corp_name'] == myCorp['name']:
            myCorp['corp_code'] = item['corp_code']
            myCorp['stock_code'] = item['stock_code']

    # Entry 값 픽스
    cont1_CC_ent.configure(state='abled')
    cont1_SC_ent.configure(state='abled')
    cont1_CC_ent.insert(0, myCorp['corp_code'])
    cont1_SC_ent.insert(0, myCorp['stock_code'])
    for i, label in enumerate([cont1_name_ent, cont1_start_year_ent, cont1_CC_ent, cont1_SC_ent]):
        label.configure(state='disabled')

    # 검색한 회사의 2018 ~ 2020 사업보고서 불러오기
    URL_MY_CORP = 'https://opendart.fss.or.kr/api/fnlttSinglAcnt.json'
    MY_CORP_PARAMS = {
        'crtfc_key': API_KEY,
        'corp_code': myCorp['corp_code'],  # 삼성전자 고유번호
        'bsns_year': myCorp['start_year'],  # 사업연도(4자리)
        'reprt_code': '11011',  # 사업보고서
    }
    resMyCorp = requests.get(url=URL_MY_CORP, params=MY_CORP_PARAMS)

    # http 정상응답시 처리
    if resMyCorp.status_code == 200:
        consoleLoging(cont2_text, END, "http 정상 응답 (res=200)\n")
        corpDataJson = resMyCorp.json()

        # output
        corpDataStr = json.dumps(corpDataJson, indent=4, ensure_ascii=False)
        print(corpDataStr)  # 전체 회사 리스트
        if corpDataJson['status'] == "000":
            detail = corpDataJson['list']
            for item in detail:  # 자산총계
                if item['fs_div'] == 'CFS' and item['sj_div'] == 'BS' and item['account_nm'] == '자산총계':
                    TA = item
            for item in detail:  # 부채총계
                if item['fs_div'] == 'CFS' and item['sj_div'] == 'BS' and item['account_nm'] == '부채총계':
                    TB = item
            for item in detail:  # 매출액 정리
                if item['fs_div'] == 'CFS' and item['sj_div'] == 'IS' and item['account_nm'] == '당기순이익':
                    SR = item
            for item in detail:  # 당기순이익 정리
                if item['fs_div'] == 'CFS' and item['sj_div'] == 'IS' and item['account_nm'] == '매출액':
                    NPDT = item
        else:
            print(corpDataJson['message'])
    else:
        print("http 통신이 정상적으로 처리되지 않았습니다.")

    # 부채비율 계산 { 부채비율 = (부채총계 / 자산총계) * 100 }
    TA_1 = int(TA['bfefrmtrm_amount'].replace(",", ""))  # (ex = 2018)
    TB_1 = int(TB['bfefrmtrm_amount'].replace(",", ""))
    TA_2 = int(TA['frmtrm_amount'].replace(",", ""))  # (ex = 2019)
    TB_2 = int(TB['frmtrm_amount'].replace(",", ""))
    TA_3 = int(TA['thstrm_amount'].replace(",", ""))  # 가장 최근년도 (ex = 2020)
    TB_3 = int(TB['thstrm_amount'].replace(",", ""))

    DR.append(calcDeptRatio(TB_1, TA_1))
    DR.append(calcDeptRatio(TB_2, TA_2))
    DR.append(calcDeptRatio(TB_3, TA_3))

    makeGragh(TA, "TA", cont3_canvas1, "Year", "Total Asset", "#a2ded0")
    makeGragh(TB, "TB", cont3_canvas2, "Year", "Total Dept", "#c8f7c5")
    makeGragh(SR, "SR", cont3_canvas3, "Year", "Sales Revenue", "#ffffcc")
    makeGragh(NPDT, "NPDT", cont3_canvas4, "Year", "Net Profit During the Term", "#c5eff7")

    consoleLoging(cont2_text, END, "Main fucntion 종료\n")
#==========================================================================================================

# Window 설정
style = Style(theme='minty')
window = style.master

window.title('Simple data entry form')
window.geometry('1600x800')
window.resizable(False, False)
window.columnconfigure(0, weight=1)
window.rowconfigure(0, weight=1)

# Form headers
form_header = ttk.Label(window, text="주린이-재무제표 분석")
form_header.place(x=30, y=10)

# Contens 1 frame======================================================
cont1 = ttk.LabelFrame(window)
cont1.config(width=440, height=240, text='Corporation Information', style='TLabelframe')
cont1.place(x=10, y=40)

## Contents form=======================================================
###- Corp name
cont1.name = StringVar(value='')
cont1_name_label = ttk.Label(cont1, text='Name', width=15, anchor='center', style='info.Inverse.TLabel')
cont1_name_label.place(x=10, y=6)
cont1_name_ent = ttk.Entry(cont1, textvariable=cont1.name, width=40)
cont1_name_ent.place(x=130, y=2)

###- Corp Year
cont1.start_year = StringVar(value='')
cont1_start_year_label = ttk.Label(cont1, text='Year', width=15, anchor='center', style='info.Inverse.TLabel')
cont1_start_year_label.place(x=10, y=49)
cont1_start_year_ent = ttk.Entry(cont1, textvariable=cont1.start_year, width=40)
cont1_start_year_ent.place(x=130, y=45)

###- Corp code
cont1_CC_label = ttk.Label(cont1, text='Corp code', width=15, anchor='center', style='info.Inverse.TLabel')
cont1_CC_label.place(x=10, y=92)
cont1_CC_ent = ttk.Entry(cont1, width=40)
cont1_CC_ent.configure(state="disabled")
cont1_CC_ent.place(x=130, y=88)

###- Stock code
cont1_SC_label = ttk.Label(cont1, text='Stock code', width=15, anchor='center', style='info.Inverse.TLabel')
cont1_SC_label.place(x=10, y=135)
cont1_SC_ent = ttk.Entry(cont1, width=40)
cont1_SC_ent.configure(state="disabled")
cont1_SC_ent.place(x=130, y=131)

###- Content 1 submit / reset button==================================
submitButton = ttk.Button(cont1, text="Submit", command=lambda:get_form_data(cont1), style='success.TButton')
submitButton.place(x=300, y=180)

resetButton = ttk.Button(cont1, text="Reset", command=lambda:resetForm(), style='warning.TButton')
resetButton.place(x=370, y=180)

# Contens 2 frame======================================================
cont2 = Frame(window)
cont2.config(padx=5, bg='#e8ecf1', highlightthickness=2, highlightbackground="#bfbfbf")
cont2.place(x=10, y=290)
cont2_label = ttk.Label(
            cont2,
            text='Console',
            width=60,
            style='info.Inverse.TLabel')
cont2_label.grid(row=0, columnspan=2, pady=10)

## Contents 2 form variables=========================================
cont2_text = Text(cont2, width=58, height=28)
cont2_text.configure(state='disabled')
cont2_text.grid(row=1, column=0, sticky='news')

# Contens 3 frame======================================================
cont3 = Frame(window)
cont3.config(padx=5, bg='#e8ecf1', highlightthickness=2, highlightbackground="#bfbfbf")
cont3.place(x=460, y=48)
cont3_label = ttk.Label(
    cont3,
    text='Graph',
    width=158,
    style='info.Inverse.TLabel')
cont3_label.grid(row=0, columnspan=2, pady=5)

## Contents 3 form variables=========================================================================
cont3_canvas1 = Canvas(cont3)
cont3_canvas2 = Canvas(cont3)
cont3_canvas3 = Canvas(cont3)
cont3_canvas4 = Canvas(cont3)
cont3_canvas1.grid(row=1, column=0, padx=2, pady=2, sticky='news')
cont3_canvas2.grid(row=1, column=1, padx=2, pady=2, sticky='news')
cont3_canvas3.grid(row=2, column=0, padx=2, pady=(2, 5), sticky='news')
cont3_canvas4.grid(row=2, column=1, padx=2, pady=(2, 5), sticky='news')

consoleLoging(cont2_text, END, "window 시작\n")


window.mainloop()

