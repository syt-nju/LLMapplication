import json
import gradio as gr
import requests
from sympy import  Eq, solve,sympify
import math
import re
import akshare as ak
import json
temperature=0.01
import pandas as pd
#找到计算式并且计算
def find_expr(text):
    text=text.replace(' ','')
    patterns = [
        r'\d+[\+\-\*\/]\d+=\d+'
    ]
    patterns=patterns[::-1]
    results = []
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            results.append(match.group())
    
    return results
    
#提取方程,返回值为一个列表，None是匹配失败,否则为对应的方程
def find_equation(text):
    text=text.replace(' ','')
    patterns = [
        r'x=\d+$',
        r'x[\+\-\*\\/]\d+=\w+',
        r'x+[\+\-\*\\/]\w+=\w+[\+\-\*\\/]\w+',
        r'x=\w+[\+\-\*\\/]\w+',
        r'x+[\+\-\*\\/]\w+=\w+[\+\-\*\\/]\w+',
        r'x+[\+\-\*\\/]\w+=\w+[\+\-\*\\/]\w+[\+\-\*\\/]\w+',
        r'x+=\w+[\+\-\*\\/]\w+[\+\-\*\\/]\w+',
        r'x+[\+\-\*\\/]\w+[\+\-\*\\/]\w+0=\w+',
        r'x\+\(x\+\d+\)=\d+',#第二题专属补丁
        r'x\+x\+\d+=\d+',
        r'x\*\d+\+\(\d+\-x\)\*\d+=\d+'#鸡兔x*2+(5260-x)*4=20264
        r'x=\d\*\*\(\d+\+\d+\)',#细胞x=3**(21+1)
        r'x\*\d+\.\d+\+\d+\.\d+=x\+\d+\.\d+',#月利润x*2.52+5.685=x+43.233
        r'y=\d+\.\d+\+\d+\.\d+\+\d+\.\d+',#月利润第二步
    ]
    patterns=patterns[::-1]
    results = []
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            results.append(match.group())
    
    return results
#将得到回复的过程包装起来，输入为完整的text，返回值为回复
def send(text:str):
    string = json.dumps({"text": text, "temperature": temperature})
    r = requests.post("http://210.28.135.34:8999/glm", data=string, headers={
        "Content-Type": "application/json"
    })
    response=r.json()['result']
    return response
#解方程函数
def solve_equation(equation_str):
    # 解析输入的方程字符串
    equation = Eq(*map(sympify, equation_str.split('=')))
    # 获取方程中的变量
    variables = equation.free_symbols
    # 解方程
    variable = variables.pop()
    solution = solve(equation, variable)
    if solution:
        return solution[0]
    else:
        return "无解"

#对输入的response进行处理，对其中的calculate进行调用并替换成回复

def solve_response(s:str):
    pattern = r'solve\(([^()]+)\)'

    while re.search(pattern, s):
        match = re.search(pattern, s)
        expr = match.group(1)
        result = solve(expr)
        if result is None:
            # 如果无法计算结果，则直接返回原字符串
            return s
        s = s[:match.start()] + str(result) + s[match.end():]

    return s
with gr.Blocks() as demo:
    gr.Markdown('请选择模式')
    with gr.Tab('简单一步计算模式'):
        chatbot = gr.Chatbot()
        msg = gr.Textbox()
        clear = gr.ClearButton([msg, chatbot])
        def respond(message, chat_history):
            text = ""
            for m, bm in chat_history:
                text += f"用户: {m}\nAI: {bm}"
            text += f"用户: {message}\nAI: "
            systext='''请你模仿下面的三个例子，只能用一元方程的方法回答问题，x的值用'x='来表示
    例1：
    问题：服装厂原来做一套衣服用布3.2米，改进裁剪方法后，每套衣服用布2.8米。原来做791套衣服的布，现在可以做多少套？
    回答：设现在可以做x套，则原来用布3.2*791米，则x*2.8=3.2*791，解得x=904.0000000000001,向下取整，最终结果为904.
    例2：
    问题：小华每天读125196页书，962天读完了《红岩》一书。小明每天读41732页书，几天可以读完《红岩》？     
    回答：设x天可以读完，小华最多读了125196*962页书，则x*41732=125196*962，解得x=2886,所以2886天可以读完
    例3：
    问题：今年植树节这天，某小学1957名师生共植树2391454棵，照这样计算，全县86524名师生共植树多少棵？
    回答：设全县86524名师生共植树x棵，则x/86524=2391454/1957,解得x=105732328.0,所以全县86524名师生共植树105732328棵
    例4：
    问题：鸡和兔共5260只，一共有20264条腿，问鸡有多少只？
    设鸡有x只，则兔子有5260-x只，则x*2+(5260-x)*4=20264，解得x=388,所以有388只鸡
    例5：问题：每个细胞每天可以分裂为3个细胞。假如一开始有3个细胞，3周后有多少细胞？
    回答：设三周后有x个细胞，三周总共21天，每过一天数量翻三倍，则x=3**(21+1)，解得x=31381059609,所以三周后有31381059609个细胞
            '''
            response=send(systext+text)
            response=response.replace(' ','')
            equations=find_equation(response)
            print(equations)
            for i in equations:
                if i!=None:
                    spot=response.find('解得')
                    print(i)
                    response=response[:spot]+'解得x='+str(solve_equation(i))+'，'
                    print(solve_equation(i))
                    break
            # print('response:',response)
            bot_message =response+send(text+'\n'+response)
            # print('bot:',bot_message)
            chat_history.append((message, bot_message))
            return "", chat_history

        msg.submit(respond, [msg, chatbot], [msg, chatbot])
    with gr.Tab('复杂两步计算模式'):     
        chatbot = gr.Chatbot()
        msg = gr.Textbox()
        clear = gr.ClearButton([msg, chatbot])

        def least_to_most_respond(message,chat_history):
            def get_final_q(text:str):
                '''以初始问题为输入，得到最终问题和条件的元组（前面是条件）'''
                rev=''.join(reversed(text))
                spot=len(text)-1-rev.find('，')
                question=text[spot+1:]
                condition=text[:spot]
                return condition,question
            def stage1(message):
                '''输入为问题，输出为第一个subquestion'''
                before='''请学习下面这一个用三箭头包括的示例，用一句话回答问题。
                <<<问题：商场改革经营管理办法后，本月盈利比上月盈利的2.52倍还多5.685万元，又知本月盈利比上月盈利多43.233万元，求这两个月盈利之和多少万元？
                回答：要解决这个问题需要先求出上月的盈利。>>>
                '''
                after='\n回答：要解决这个问题需要先求出'
                response=send(before+message+after)
                subq1=response[:response.find('。')]
                return subq1
            def stage2(condition,subq1):
                '''将subq1算出，然后用respond中的操作将response截断在解得，返回'''
                text=condition+'，求'+subq1+'？'
                before='''请你模仿下面的例子，只能用一元方程的方法回答问题，x的值用'x='来表示
                例:
                    问题：商场改革经营管理办法后，本月盈利比上月盈利的2.52倍还多5.685万元，又知本月盈利比上月盈利多43.233万元，求上月的盈利？
                    回答：设上月盈利为x,则本月盈利为x*2.52+5.685万元，则x*2.52+5.685=x+43.233,解得x=24.702631578947365万元，所以上月的盈利为24.702631578947365万元。
                    
                '''
                after=''
                response=send(before+text+after)
                response=response.replace(' ','')
                equations=find_equation(response)
                print(equations)
                if len(equations)>0:
                    for i in equations:
                        if i!=None:
                            spot=response.find('解得')
                            print(i)
                            response=response[:spot]+'解得x='+str(solve_equation(i))+'，'
                            print(solve_equation(i))
                            break
                else:
                    exprs=find_expr(response)
                    for i in exprs:
                        print('shit:',i)
                        spot=response.find('=')
                        response=response[:spot]+'='+str(eval(i))       
                    
                return response
            def stage3(message,r1):
                before='''请你模仿下面的例子，只能用一元方程的方法回答问题，x的值用'x='来表示
                例:
                    问题：商场改革经营管理办法后，本月盈利比上月盈利的2.52倍还多5.685万元，又知本月盈利比上月盈利多43.233万元，求这两个月盈利之和多少万元？
                    回答：设上月盈利为x,则本月盈利为x*2.52+5.685万元，则x*2.52+5.685=x+43.233,解得x=24.702631578947365万元，所以上月的盈利为24.702631578947365万元。不妨再设两月盈利和为y万元，则y=24.702631578947365+24.702631578947365+43.233解得y=92.63826315789473,所以两个月盈利和为92.63826315789473万元
                    
                '''
                after=''
                response=send(before+message+'\n'+r1+after)
                equations=find_equation(response)
                print('response',response)
                print(equations)
                if len(equations)>0:
                    for i in equations:
                        if i!=None:
                            spot=response.find('解得')
                            print(i)
                            response=response[:spot]+'解得y='+str(solve_equation(i))+'，'
                            print(solve_equation(i))
                            break
                else:
                    exprs=find_expr(response)
                    for i in exprs:
                        print('shit:',i)
                        spot=response.find('=')
                        response=response[:spot]+'='+str(eval(i[:i.find('=')]))
                return r1+response

                 
            text =message        
            condition,final_q=get_final_q(text)
            subq1=stage1(message)
            print(subq1)
            r1=stage2(condition,subq1)
            print('r1:',r1)
            final_r=stage3(message,r1)
            bot_message =final_r+send(message+'\n'+final_r)
            # print('bot:',bot_message)
            chat_history.append((message, bot_message))
            return "", chat_history
        msg.submit(least_to_most_respond, [msg, chatbot], [msg, chatbot])
    with gr.Tab('A股历史股价走势查询'):
        def plot_lines(text):
            before='''请模仿下面的例子提取文本的信息并且以Json形式回复。
            例1：{
                    "stock": "国泰环保",
                    "start_date": "20230803", 
                    "end_date": "20230807"
                }
                >>>
    请求： '''
            after='\n'+'回复：'
            response=send(before+text+after)
            start=response.find('{')
            end=response.find('}')
            response=response[start:end+1]
            print(response)
            res_dic=json.loads(response)
            df = ak.stock_zh_a_spot_em()
            code = df.loc[df['名称'] == res_dic['stock'], '代码'].values[0]
            stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=res_dic['start_date'], end_date=res_dic['end_date'], adjust="")
            stock_zh_a_hist_df["日期"] = stock_zh_a_hist_df["日期"].apply(lambda date: date.strftime('%Y-%m-%d'))
            new_columns = ['价格', 'label','日期']
            new_df = pd.DataFrame(columns=new_columns)
            new_df['日期'] = stock_zh_a_hist_df['日期'].repeat(2)
            for i in new_df.index:
                if i%2!=0:
                    new_df['label'][i]='开盘'
                    new_df['价格'][i]=stock_zh_a_hist_df['开盘'][(i+1)/2]
                else:
                    new_df['label'][i]='收盘'
                    new_df['价格'][i]=stock_zh_a_hist_df['收盘'][i/2]
            # 打印新的 DataFrame
            print(new_df)
            return new_df
        textbox=gr.Textbox()
        output=gr.LinePlot(
            x="日期",
            y='价格',
            color="label",
            color_legend_position="bottom",
            title="Stock Prices",
            tooltip=["日期", "价格",'label'],
            height=300,
            width=500
        )
        btn = gr.Button(value="确认")
        btn.click(plot_lines, textbox, output)


    





if __name__ == "__main__":
    demo.launch()
