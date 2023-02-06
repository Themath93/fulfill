
from dicts_cy import return_dict
from oracle_connect import DataWarehouse


import xlwings as xw
import pandas as pd
import os
from datetime import datetime
from barcode import Code128
from barcode.writer import ImageWriter

wb_cy = xw.Book.caller()
# wb_cy = xw.Book('cytiva.xlsm')


## 선택한 행, 시트 이름 딕셔너리로 반환
def row_nm_check(xw_book_name=xw.books[0]):
    """
    Return Dict, get activated sheet's name(str), get selected row's number(list)

    each_list는 연속된 row번호들을 전부 계산하여 리스트안에 전부 각각 위치하도록 한다.
    each_list의 모든 값은 int
    """
    ## SpecialCells(12) 셀이 한개만 클릭됬을 경우에는 제대로 작동 불가

    # 셀한개만 클릭할경우 $의 개수가 2개이고 2개이상일경우 $의 개수는 4개 이다.
    sel_cell = xw_book_name

    count_dollar = sel_cell.selection.address.count("$")
    
    # 셀한개만 클릭할경우
    if count_dollar == 2 :
        
        sel_rng = [sel_cell.selection.address]
    else : 
    
        sel_rng = xw_book_name.selection.api.SpecialCells(12).Address.split(",")
    
    range_list = []
    
    for rng in sel_rng:

        if ":" in rng:
            num_0 = rng.split(":")[0].split("$")[-1]
            num_1 = rng.split(":")[1].split("$")[-1]
            #범위선택이 한 컬럼이 아닌 여러 컬럼을 동시에 선택된 경우
            if num_0 == num_1 :
                range_list.append(num_0)
            else : 
                range_list.append(str(num_0) + ',' + str(num_1))
        else :
            range_list.append(rng.split("$")[-1])

    fin_list = []
    for rng_val in range_list:
        if ',' in rng_val:
            tmp_split = rng_val.split(',')
            cnts = int(tmp_split[1])-int(tmp_split[0])
            tmp_list = []
            for i in range(cnts+1):
                tmp_list.append(int(tmp_split[0])+i)
                
            fin_list = fin_list + tmp_list
        else :
            fin_list.append(int(rng_val))
            
    dict_row_num_sheet_name = {"sheet_name":xw_book_name.selection.sheet.name,'selection_row_nm':range_list,'each_list':fin_list}
    
    
    return dict_row_num_sheet_name


## 출고행 번호 리스트 -> 문자열로 변환
def get_row_list_to_string(seleted_row_list) :
    return ' '.join(seleted_row_list).replace(',','~').replace(' ', ', ')


## 출고 form 초기화 및 출고 대기상태로 변경
def clear_form(sheet = wb_cy.selection.sheet):
    current_sheet = sheet
    protect_sht_pass = 'themath93'
    #통합제어 시트일 경우
    if current_sheet.name == '통합제어' :

        main_clear('SVC')
    else :
        try:
            __xl_clear_values(current_sheet)
        except :
            current_sheet.api.Unprotect(Password='themath93')
            protect_sht(current_sheet,protect_sht_pass)
            __xl_clear_values(current_sheet)
            if current_sheet.name == 'Shipment information':
                # si_index컬럼 기준으로 오름차순 정렬 -> so_out시 excel 내용 업데이트에 반드시필요
                last_row = sheet.range("A1048576").end('up').row
                sheet.range((9,'A'),(last_row,'R')).api.Sort(Key1=sheet.range((9,'A')).api, Order1=1, Header=1, Orientation=1)
            

def __xl_clear_values(current_sheet):
    ws_db = wb_cy.sheets['Temp_DB']
    tmp_last_row = get_empty_row(ws_db,"T")-1
    k = ws_db.range((2,"T"),(tmp_last_row,"T")).value
    # tmp_dict = dict(zip(k,v))
    # wb_cy.app.alert(k[0])
    for sht_name in k:
        # wb_cy.app.alert(sht_name)
        if current_sheet.name == sht_name :
            k_idx = k.index(current_sheet.name)
            # wb_cy.app.alert(str(k_idx))
            k_row = 2+k_idx
            ws_db.range((k_row,"U")).clear_contents()

    status_cel = current_sheet.range("AAA4").end('left')
    current_sheet.range("C2:C7").clear_contents()
    status_cel.color = None
    status_cel.value = "waiting_for_out"
    current_sheet.range("C4").value = "=TODAY()+1"


def main_clear(type=None):
    """
    통합제어 시트 from클리어 매서드
    """
    ws_main =wb_cy.sheets['통합제어']

    if type != None:
        
        shapes = ws_main.shapes
        last_row = get_empty_row(ws_main,'J')
        for shp in shapes :
            if type in shp.name :
                shp.delete()

        ws_main.range("J12:S"+str(last_row)).clear_contents()
    else :
        pass



def get_idx(sheet_name):
    """
    xlwings.main.Sheet를 인수로 입력

    get_each_index_num 모듈의 반대로 반환함
    example : get_idx_str='si_13384A14171A14243C14244'  ==>
    {'out_sht_id':'si','idx_list':[13384, 14171, 14243, 14244]}

    [13384, 14171, 14243, 14244] -> '13384A14171A14243C14244'
    
    """
    # 연속된 숫자 표현

    # 'c'는 연속된 숫자, 'd'는 분리필요

    idx_list = get_out_table(sheet_name)

    idx_cal = [idx_list[0]]
    tmp = idx_list[0]
    for val in idx_list:
        if tmp == val:
            continue
        elif tmp == val - 1 :
            idx_cal.append('c')
            tmp = val
        else :
            idx_cal.append('d')
            idx_cal.append(val) 
            tmp = val
    
    idx_cal = list(map(str, idx_cal))
    d_count = idx_cal.count('d')

    idx_done = ''.join(idx_cal).split('d')
    idx_list_fin = []

    
    fin_idx = return_dict(1)[sheet_name.name]
    
    for idx in range(d_count+1):
        val = idx_done[idx]
        if 'c' in val :
            c_count = val.count('c')
            val = val.replace('c','')
            idx_list_fin.append(val + 'C' +str(int(val) + c_count))
        else :
            idx_list_fin.append(val)

    fin_idx = fin_idx + '_'+'A'.join(idx_list_fin)

    return fin_idx


#############################################################################
def get_out_table(sheet_name,index_row_number=9):
    """
    xlwings.main.Sheet를 인수로 입력, 해당시트의 index행번호 default = 9 (int)
    list형태의 출고하는 시트의 index들을 반환한다.
    """
    out_row_nums = sheet_name.range("C2").options(numbers=int).value
    col_count = sheet_name.range("XFD9").end('left').column
    idx_row_num = index_row_number
    col_names = sheet_name.range(sheet_name.range(int(idx_row_num),1),sheet_name.range(int(idx_row_num),col_count)).value
    
    for idx ,i in enumerate(col_names):
        
        if i == None:
            continue
        elif '_INDEX' in i :
            col_num = idx
    
    df_so = pd.DataFrame()
    
    try :
        row_list = out_row_nums.replace(' ','').split(',')
    except:
        row_list = [out_row_nums]
    
    for row in row_list :

        # 연속된 행인 경우
        if '~' in str(row) :
            left_row =int(row.split('~')[0])
            right_row = int(row.split('~')[1])
            rng = sheet_name.range(sheet_name.range(left_row,1),sheet_name.range(right_row,col_count))
            df_so = pd.concat([df_so,pd.DataFrame(sheet_name.range(rng).options(numbers=int).value)]) 
        else :
            left_row =int(row)
            right_row = int(row)
            rng = sheet_name.range(sheet_name.range(left_row,1),sheet_name.range(right_row,col_count))
            df_so = pd.concat([df_so,pd.DataFrame(sheet_name.range(rng).options(numbers=int).value).T])

    
    return list(df_so[col_num])



# 
def get_out_info(sheet_name):
    
    #2 배송방법 3 인수증방식
    info_list = sheet_name.range("C3:C7").value
    info_list[1]=str(info_list[1].date().isoformat())
    # 배송방법, 인수증방식은 DB에서 해당 내용으로 키값을 받아 DB에저장 -> byte사용이적어 용량에 유리
    info_list[2] = get_tb_idx('DELIVERY_METHOD',info_list[2])
    info_list[3] = get_tb_idx('POD_METHOD',info_list[3])

    now= str(get_current_time())
    info_list.append(now)
    # tmp_idx = str(wb_cy.sheets['temp_db'].range("C500000").end('up').row -1 )
    out_idx = None
    
    if sheet_name.range("C2").value == 'only_local':
        
        info_list.insert(0,'only_local')
    else :
        info_list.insert(0,get_idx(sheet_name))

    info_list.insert(0,out_idx)

    return info_list


## 시트보호 잠금 및 해제 매서드

def sht_protect(mode=True):
    """
    True 이면 시트보호모드, False 이면 시트보호해제
    """
    wb = xw.Book.caller()
    act_sht=wb_cy.selection.sheet
    status_col = act_sht.range("XFD4").end('left').column
    status_cel = act_sht.range(4,status_col)
    password = 'themath93'

    if mode == True:

        if status_cel.value != 'edit_mode' :
            wb_cy.save()
            act_sht.api.Unprotect(Password = password)

            # status창 변경
            status_cel.value = 'edit_mode'

        else : 
            clear_form()
            protect_sht(act_sht,password)

            # status창 변경



    elif mode == False:
        wb_cy.save()
        act_sht.api.Unprotect(Password='themath93')

        # status창 변경
        status_cel.value = 'edit_mode'

def protect_sht(act_sht,password):
    act_sht.api.Protect(Password=password, DrawingObjects=True, Contents=True, Scenarios=True,
            UserInterfaceOnly=True, AllowFormattingCells=True, AllowFormattingColumns=True,
            AllowFormattingRows=True, AllowInsertingColumns=True, AllowInsertingRows=True,
            AllowInsertingHyperlinks=True, AllowDeletingColumns=True, AllowDeletingRows=True,
            AllowSorting=True, AllowFiltering=True, AllowUsingPivotTables=True)
    



def get_empty_row(sheet=wb_cy.selection.sheet,col=1):
    """
    특정컬럼의 값이 있는 마지막 행 + 1을 반환
    """
    sel_sht = sheet
    col_num = col
    if type(col) == int :
        row_start_nm = sel_sht.range(1048576,col_num).end('up').row + 1 
    elif type(col) == str :
        row_start_nm = sel_sht.range(col+str(1048576)).end('up').row + 1 
    return row_start_nm


def get_current_time():
    """
    현재시간 년,월,일 시,분,초 반환
    """
    now = str(datetime.now()).split('.')[0]

    return now



def save_barcode_loc(index=str):
    """
    받은 index(str)을 바코드 이미지로 만들어 저장
    """
    file_name = index+".jpeg"
    render_options = {
                    "module_width": 0.05,
                    "module_height": 9.5,
                    "write_text": True,
                    "module_width": 0.25,
                    "quiet_zone": 0.1,
                }

    barcode=Code128(index,writer=ImageWriter()).render(render_options)
    barcode.save(file_name)
    pic = '\\'+file_name
    pic = os.getcwd()+pic
    return pic


def get_tb_idx(tb_name=str, content=str):
    """
    DW의 table이름을, content에는 테이블의 content를 입력하면 tb상 key값을 반환한다.
    """
    cur = DataWarehouse()
    dic_dm = dict(cur.execute(f'select * from {tb_name}').fetchall())
    dic_dm = dict(zip(list(dic_dm.values()),list(dic_dm.keys())))
    return dic_dm[content]


def get_each_index_num(get_idx_str):
    """
    DW테이블 SO_OUT상의 si_index 및 is_local 컬럼값을 넣으면 해당 row의 고유 키값을 dict형태로 반환

    example : get_idx_str='si_13384A14171A14243C14244'  ==>
    {'out_sht_id':'si','idx_list':[13384, 14171, 14243, 14244]}
    """
    del_sht_id = get_idx_str.split('_')[0]
    get_idx_str = get_idx_str.split('_')[1]
    count_A = get_idx_str.count("A")
    count_C = get_idx_str.count("C")
    if count_A == 0 and count_C == 0:
        return get_idx_str
    procs_1 = get_idx_str.split("A")
    procs_1
    A_list = []
    C_list = []
    for val in procs_1:
        if val.count("C") > 0 :
            C_list.append(val)
        else :
            A_list.append(int(val))
    
    for c_val in C_list:      
        tmp_c = c_val.split('C')
        tmp_diff = int(tmp_c[1])-int(tmp_c[0])
        fin_C_list = []
        for i, val in enumerate(range(tmp_diff+1)):
            fin_C_list.append(int(tmp_c[0]) + i)
        A_list = A_list+fin_C_list
            
    return {'out_sht_id':del_sht_id,'idx_list':A_list}


    

def get_xl_rng_for_ship_date(xl_selection = wb_cy.selection,  ship_date_col_num=str):
    """
    sheet.range(ship_date_col_xl_rng_list)
    ship_date_col_num는 해당 시트의 ship_date컬럼의 알파벳 입력하면됨
    range를 위한 str를 반환 객체를 반환하는 것은 아님
    """

    count_dollar = xl_selection.api.Address.count("$")
    count_dollar
    # 셀한개만 클릭할경우
    if count_dollar == 2 :

        rng_str = xl_selection.api.Address
    else : 

        rng_str = xl_selection.api.SpecialCells(12).Address

    rng_str_1 = rng_str.replace('$','')
    comma_spt = rng_str_1.split(',')

    for idx, rng in enumerate(comma_spt):
        if ':' in rng:
            colon_idx = rng.index(':')
            alpha_0 = rng[0]
            alpha_1 = rng[colon_idx+1]
            comma_spt[idx] = comma_spt[idx].replace(alpha_0,ship_date_col_num)
            comma_spt[idx] = comma_spt[idx].replace(alpha_1,ship_date_col_num)
        else:
            alpha_0 = rng[0]
            comma_spt[idx] = comma_spt[idx].replace(alpha_0,ship_date_col_num)
    rng_fin = ','.join(comma_spt)
    return rng_fin



##### change_cell 모듈 ######################### cell한개의 내용 변경########
def select_cell():
    sel_cells = wb_cy.selection
    sel_sht = wb_cy.selection.sheet
    # 선택한 셀의 row번호가 10미만이면 종료 ==> table값은 row가 10부터 시작이기 때문
    if wb_cy.selection.row < 10 :
        wb_cy.app.alert("선택한 셀은 바꿀 수 없습니다. 매서드를 종료합니다.","Change Cell WARNING")
        return None
    address_cell = sel_sht.range("E3")
    from_cell = sel_sht.range("E4")
    # 선택한셀의 value가 list type 이면 두 개이상의 셀을 선택 했다는 것 ==> 종료
    if type(sel_cells.value) is list :
        wb_cy.app.alert("하나의 셀만 선택 후 진행해주세요. 두 개 이상은 불가합니다.","Change Cell WARNING")
        return None
    
    address_cell.value = str(sel_cells.address)
    from_cell.value = sel_cells.value

def change_cell():
    sel_sht = wb_cy.selection.sheet
    address_cell = sel_sht.range("E3")
    change_cell_list = sel_sht.range("E3:E4")
    tb_name = sel_sht.range("D5").value
    idx_col_name = sel_sht.range("A9").value
    cur = DataWarehouse()
    
    # 셀주소가 빈값이면 중지한다.
    if address_cell.value == None:
        wb_cy.app.alert("바꿀 셀이 없습니다 매서드를 종료합니다","Change Cell WARNING")
        return None
    
    xl_from_cell = sel_sht.range(address_cell.value)
    to_cell = wb_cy.app.api.InputBox("바꿀 내용을 입력 해주세요", "Change Cell Input", Type=2)
    # to_cell == False면 입력을 취소 했다는 뜻이므로 바꿀 뜻이 없는 것으로 간주하고 주소와 바뀔 값들의 form을 지운다.
    if to_cell == False :
        wb_cy.app.alert("취소를 선택하셨습니다. 셀 변경을 취소합니다.","Change Cell WARNING")
        change_cell_list.clear_contents()
        return None
    
    # DB UPDATE 진행
    row_num = sel_sht.range(address_cell.value).row
    col_mum = sel_sht.range(address_cell.value).column
    idx_num = sel_sht.range(row_num,1).options(numbers=int).value
    col_name = sel_sht.range(9,col_mum).options(numbers=int).value
    query = f"UPDATE {tb_name} SET {col_name} = '{to_cell}' WHERE {idx_col_name} = {idx_num}"
    cur.execute(query)
    cur.execute("commit")
    
    # DB UPDATE 완료 후 xl_cell 내용 변경
    xl_from_cell.value = to_cell
    
    # 모든게 완료 되면 change_cell_list 내용 모두삭제
    change_cell_list.clear_contents()

    # 변경 성공 메시지
    wb_cy.app.alert("셀 내용 변경이 완료되었습니다.","Change Cell Done")
##### change_cell 모듈 ######################### cell한개의 내용 변경########