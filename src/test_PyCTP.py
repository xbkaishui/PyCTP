# -*- coding: utf-8 -*-
"""
Created on Sat Jul 30 17:19:21 2016

@author: zhuolin
"""

import sys
import threading
import PyCTP

class InfoField:
    """返回信息"""

    def __init__(self):
        """Constructor"""
        '''错误号'''
        self.ErrorID = 0
        '''错误号'''
        '''错误描述'''
        self.ErrorMsg = '正确'
        '''错误描述'''

    def __str__(self):
        # return 'ErrorID:{0}, ErrorMsg:{1}'.format(self.ErrorID, self.ErrorMsg)
        return '{{"ErrorID":{self.ErrorID}, "ErrorMsg":"{self.ErrorMsg}"}}'.format(
            self=self)

    @property
    def __dict__(self):
        return {'ErrorID': self.ErrorID, 'ErrorMsg': str(self.ErrorMsg, 'GB2312')}


class PyCTP_Market_API(PyCTP.CThostFtdcMdApi):

    TIMEOUT = 30
    
    __RequestID = 0
    __isLogined = False
    
    def __IncRequestID(self):
        """ 自增并返回请求ID """
        #self.__RequestID += 1
        return self.__RequestID
        
    def setInvestorID(self, InvestorID):
        self.__InvestorID = InvestorID
        return self.__InvestorID
        
    def Connect(self, frontAddr):
        """ 连接前置服务器 """
        self.RegisterSpi(self)
        self.RegisterFront(frontAddr)
        self.Init()
        self.__rsp_Connect = dict(event=threading.Event())
        self.__rsp_Connect['event'].clear()
        return 0 if self.__rsp_Connect['event'].wait(self.TIMEOUT) else -4

    def Login(self, BrokerID, UserID, Password):
        """ 用户登录请求 """
        reqUserLogin = dict(BrokerID    = BrokerID
                            , UserID    = UserID
                            , Password  = Password)
        self.__rsp_Login = dict(event       = threading.Event()
                                , RequestID = self.__IncRequestID())
        ret = self.ReqUserLogin(reqUserLogin, self.__rsp_Login['RequestID'])
        if ret == 0:
            self.__rsp_Login['event'].clear()
            if self.__rsp_Login['event'].wait(self.TIMEOUT):
                if self.__rsp_Login['ErrorID'] == 0:
                    self.__isLogined = True
                    self.__BrokerID = BrokerID
                    self.__UserID   = UserID
                    self.__Password = Password
                else:
                    sys.stderr.write(str(self.__rsp_Login['ErrorMsg'], encoding='gb2312'))
                return self.__rsp_Login['ErrorID']
            else:
                return -4
        return ret
        
    def Logout(self):
        """ 登出请求 """
        reqUserLogout = dict(BrokerID   = self.__BrokerID
                            , UserID    = self.__UserID)
        self.__rsp_Logout = dict(event      = threading.Event()
                                , RequestID = self.__IncRequestID())
        ret = self.ReqUserLogout(reqUserLogout, self.__rsp_Logout['RequestID'])
        if ret == 0:
            self.__rsp_Logout['event'].clear()
            if self.__rsp_Logout['event'].wait(self.TIMEOUT):
                if self.__rsp_Logout['ErrorID'] == 0:
                    self.__isLogined = False
                return self.__rsp_Logout['ErrorID']
            else:
                return -4
        return ret
        
    def SubMarketData(self, InstrumentID):
        """ 订阅行情 """
        self.__rsp_SubMarketData = dict(results=[], ErrorID=0, event=threading.Event(), RequestID=self.__IncRequestID())
        ret = self.SubscribeMarketData(InstrumentID, len(InstrumentID))
        if ret == 0:
            self.__rsp_SubMarketData['event'].clear()
            if self.__rsp_SubMarketData['event'].wait(self.TIMEOUT):
                if self.__rsp_SubMarketData['ErrorID'] != 0:
                    return self.__rsp_SubMarketData['ErrorID']
                return self.__rsp_SubMarketData['results']
            else:
                return -4
        return ret
        
    def UnSubMarketData(self, InstrumentID):
        """ 退订行情 """
        self.__rsp_UnSubMarketData = dict(results=[], ErrorID=0, event=threading.Event(), RequestID=self.__IncRequestID())
        ret = self.UnSubscribeMarketData(InstrumentID, len(InstrumentID))
        if ret == 0:
            self.__rsp_UnSubMarketData['event'].clear()
            if self.__rsp_UnSubMarketData['event'].wait(self.TIMEOUT):
                if self.__rsp_UnSubMarketData['ErrorID'] != 0:
                    return self.__rsp_UnSubMarketData['ErrorID']
                return self.__rsp_UnSubMarketData['results']
            else:
                return -4
        return ret
        
    def OnFrontConnected(self):
        """ 当客户端与交易后台建立起通信连接时（还未登录前），该方法被调用。 """
        self.__rsp_Connect['event'].set()
    
    def OnFrontDisconnected(self, nReason):
        """ 当客户端与交易后台通信连接断开时，该方法被调用。当发生这个情况后，API会自动重新连接，客户端可不做处理。
        nReason 错误原因
        0x1001 网络读失败
        0x1002 网络写失败
        0x2001 接收心跳超时
        0x2002 发送心跳失败
        0x2003 收到错误报文        
        """
        sys.stderr.write('前置连接中断: %s' % hex(nReason))
        # 登陆状态时掉线, 自动重登陆
        #if self.__isLogined:
        #    self.__Inst_Interval()
        #    sys.stderr.write('自动登陆: %d' % self.Login(self.__BrokerID, self.__UserID, self.__Password))
        
    def OnRspUserLogin(self, RspUserLogin, RspInfo, RequestID, IsLast):
        """ 登录请求响应 """
        if RequestID == self.__rsp_Login['RequestID'] and IsLast:
            #self.__BrokerID = RspUserLogin['BrokerID']
            #self.__UserID = RspUserLogin['UserID']
            self.__SystemName = RspUserLogin['SystemName']
            self.__TradingDay = RspUserLogin['TradingDay']
            self.__DCETime = RspUserLogin['DCETime']
            self.__SessionID = RspUserLogin['SessionID'] 
            self.__MaxOrderRef = RspUserLogin['MaxOrderRef']
            self.__INETime = RspUserLogin['INETime']
            self.__LoginTime = RspUserLogin['LoginTime']
            self.__FrontID = RspUserLogin['FrontID']
            self.__FFEXTime = RspUserLogin['FFEXTime']
            self.__CZCETime = RspUserLogin['CZCETime']
            self.__SHFETime = RspUserLogin['SHFETime']
            self.__rsp_Login.update(RspInfo)
            self.__rsp_Login['event'].set()
            
    def OnRspUserLogout(self, RspUserLogout, RspInfo, RequestID, IsLast):
        """ 登出请求响应 """
        if RequestID == self.__rsp_Logout['RequestID'] and IsLast:
            self.__rsp_Logout.update(RspInfo)
            self.__rsp_Logout['event'].set()
            
    def OnRspError(self, RspInfo,  RequestID, IsLast):
        """ 错误信息 """
        sys.stderr.write(repr(([RspInfo['ErrorID'], str(RspInfo['ErrorMsg'], encoding='gb2312')], RequestID, IsLast)))
    
    def OnRspSubMarketData(self, SpecificInstrument, RspInfo, RequestID, IsLast):
        """ 订阅行情应答 """
        if RequestID == self.__rsp_SubMarketData['RequestID']:
            if RspInfo is not None:
                self.__rsp_SubMarketData.update(RspInfo)
            if SpecificInstrument is not None:
                self.__rsp_SubMarketData['results'].append(SpecificInstrument)
            if IsLast:
                self.__rsp_SubMarketData['event'].set()
                
    def OnRspUnSubMarketData(self, SpecificInstrument, RspInfo, RequestID, IsLast):
        """ 取消订阅行情应答 """
        if RequestID == self.__rsp_UnSubMarketData['RequestID']:
            if RspInfo is not None:
                self.__rsp_UnSubMarketData.update(RspInfo)
            if SpecificInstrument is not None:
                self.__rsp_UnSubMarketData['results'].append(SpecificInstrument)
            if IsLast:
                self.__rsp_UnSubMarketData['event'].set()
                
    def OnRtnDepthMarketData(self, DepthMarketData):
        """ 行情推送 """
        pass

class PyCTP_Trader_API(PyCTP.CThostFtdcTraderApi):

    TIMEOUT = 30
    
    __RequestID = 0
    __isLogined = False
    
    def __IncRequestID(self):
        """ 自增并返回请求ID """
        self.__RequestID += 1
        return self.__RequestID
    
    def __IncOrderRef(self):
        """ 递增报单引用 """
        OrderRef = bytes('%012d' % self.__OrderRef, 'gb2312')
        self.__OrderRef += 1
        return OrderRef
        
    def setInvestorID(self, InvestorID):
        self.__InvestorID = InvestorID
        return self.__InvestorID
        
    def Connect(self, frontAddr):
        """ 连接前置服务器 """
        self.RegisterSpi(self)
        self.SubscribePrivateTopic(PyCTP.THOST_TERT_RESUME)
        self.SubscribePublicTopic(PyCTP.THOST_TERT_RESUME)
        self.RegisterFront(frontAddr)
        self.Init()
        self.__rsp_Connect = dict(event=threading.Event())
        self.__rsp_Connect['event'].clear()
        return 0 if self.__rsp_Connect['event'].wait(self.TIMEOUT) else -4

    def Login(self, BrokerID, UserID, Password):
        """ 用户登录请求 """
        reqUserLogin = dict(BrokerID    = BrokerID
                            , UserID    = UserID
                            , Password  = Password)
        self.__rsp_Login = dict(event       = threading.Event()
                                , RequestID = self.__IncRequestID())
        ret = self.ReqUserLogin(reqUserLogin, self.__rsp_Login['RequestID'])
        if ret == 0:
            self.__rsp_Login['event'].clear()
            if self.__rsp_Login['event'].wait(self.TIMEOUT):
                if self.__rsp_Login['ErrorID'] == 0:
                    self.__isLogined = True
                    self.__Password = Password
                else:
                    sys.stderr.write(str(self.__rsp_Login['ErrorMsg'], encoding='gb2312'))
                return self.__rsp_Login['ErrorID']
            else:
                return -4
        return ret
        
    def Logout(self):
        """ 登出请求 """
        reqUserLogout = dict(BrokerID   = self.__BrokerID
                            , UserID    = self.__UserID)
        self.__rsp_Logout = dict(event      = threading.Event()
                                , RequestID = self.__IncRequestID())
        ret = self.ReqUserLogout(reqUserLogout, self.__rsp_Logout['RequestID'])
        if ret == 0:
            self.__rsp_Logout['event'].clear()
            if self.__rsp_Logout['event'].wait(self.TIMEOUT):
                if self.__rsp_Logout['ErrorID'] == 0:
                    self.__isLogined = False
                return self.__rsp_Logout['ErrorID']
            else:
                return -4
        return ret
      
    def Authenticate(self, BrokerID, UserID, UserProductInfo, AuthCode, AppID):
        """ 客户端认证 """
        pReqAuthenticateField = dict(BrokerID=BrokerID,
                                     UserID=UserID,
                                     UserProductInfo=UserProductInfo,
                                     AuthCode=AuthCode,
                                     AppID=AppID)
        self.__rsp_Authenticate = dict(event = threading.Event(),
                                       RequestID = self.__IncRequestID(),
                                       results   = [],
                                       ErrorID   = 0)
        ret = self.ReqAuthenticate(pReqAuthenticateField, self.__rsp_Authenticate['RequestID'])
        if ret == 0:
            self.__rsp_Authenticate['event'].clear()
            if self.__rsp_Authenticate['event'].wait(self.TIMEOUT):
                if self.__rsp_Authenticate['ErrorID'] != 0:
                    return self.__rsp_Authenticate['ErrorID']
                return self.__rsp_Authenticate['ErrorMsg'].decode('gb2312')
            else:
                return -4
        return ret
      
    def RegUserSystemInfo(self, BrokerID, UserID, ClientAppID):
        """
        注册用户终端信息，用于中继服务器多连接模式
        需要在终端认证成功后，用户登录前调用该接口
        """
        SystemInfo = PyCTP.CTP_GetSystemInfo()
        if SystemInfo['ret'] != 0: return SystemInfo['ret']
        pSystemInfo, nlen = SystemInfo['SystemInfo'], SystemInfo['nLen']
        pUserSystemInfo = dict(BrokerID = BrokerID, 
                               UserID = UserID,
                               ClientSystemInfoLen = nlen,
                               ClientSystemInfo = pSystemInfo,
                               ClientPublicIP = b'192.168.0.1',
                               ClientIPPort = 51305,
                               reserve1 = b'',
                               ClientLoginTime = b'20190121',
                               ClientAppID = ClientAppID)
        ret = self.RegisterUserSystemInfo(pUserSystemInfo)
        print( "注册用户终端信息......发送成功\n" if ret == 0 else "注册用户终端信息......发送失败，错误序号=[%d]\n" % ret );
        return ret
        
    def SubUserSystemInfo(self, BrokerID, UserID, ClientAppID):
        """
      	上报用户终端信息，用于中继服务器操作员登录模式
        操作员登录后，可以多次调用该接口上报客户信息
        """
        SystemInfo = PyCTP.CTP_GetSystemInfo()
        if SystemInfo['ret'] != 0: return SystemInfo['ret']
        pSystemInfo, nlen = SystemInfo['SystemInfo'], SystemInfo['nLen']
        pUserSystemInfo = dict(BrokerID = BrokerID,
                               UserID = UserID,
                               ClientSystemInfoLen = nlen,
                               ClientSystemInfo = pSystemInfo,
                               ClientPublicIP = b'192.168.0.1',
                               ClientIPPort = 51305,
                               reserve1 = b'',
                               ClientLoginTime = b'20190121',
                               ClientAppID = ClientAppID)
        ret = self.SubmitUserSystemInfo(pUserSystemInfo)
        print( "上报用户终端信息......发送成功\n" if ret == 0 else "上报用户终端信息......发送失败，错误序号=[%d]\n" % ret );
        return ret
      
    def QryInstrument(self, ExchangeID=b'', InstrumentID=b''):
        """ 查询和约 """
        QryInstrument = dict(ExchangeID     = ExchangeID
                            , InstrumentID  = InstrumentID)
        self.__rsp_QryInstrument = dict(event       = threading.Event()
                                        , RequestID = self.__IncRequestID()
                                        , results   = []
                                        , ErrorID   = 0)
        ret = self.ReqQryInstrument(QryInstrument, self.__rsp_QryInstrument['RequestID'])
        if ret == 0:
            self.__rsp_QryInstrument['event'].clear()
            if self.__rsp_QryInstrument['event'].wait(self.TIMEOUT):
                if self.__rsp_QryInstrument['ErrorID'] != 0:
                    return self.__rsp_QryInstrument['ErrorID']
                return self.__rsp_QryInstrument['results']
            else:
                return -4
        return ret
        
    def QryInstrumentMarginRate(self, InstrumentID):
        """ 请求查询合约保证金率 """
        QryInstrumentMarginRate = dict(BrokerID         = self.__BrokerID
                                       , InvestorID     = self.__InvestorID
                                       , InstrumentID   = InstrumentID)
        self.__rsp_QryInstrumentMarginRate = dict(results       =  []
                                                  , RequestID   = self.__IncRequestID()
                                                  , ErrorID     = 0
                                                  , event       = threading.Event())
        ret = self.ReqQryInstrumentMarginRate(QryInstrumentMarginRate, self.__rsp_QryInstrumentMarginRate['RequestID'])
        if ret == 0:
            self.__rsp_QryInstrumentMarginRate['event'].clear()
            if self.__rsp_QryInstrumentMarginRate['event'].wait(self.TIMEOUT):
                if self.__rsp_QryInstrumentMarginRate['ErrorID'] != 0:
                    return self.__rsp_QryInstrumentMarginRate['ErrorID']
                return self.__rsp_QryInstrumentMarginRate['results']
            else:
                return -4
        return ret
        
    def QryInstrumentCommissionRate(self, InstrumentID):
        """ 请求查询合约手续费率 """
        QryInstrumentCommissionRate = dict(BrokerID = self.__BrokerID, InvestorID = self.__InvestorID, InstrumentID = InstrumentID)
        self.__rsp_QryInstrumentCommissionRate = dict(results       =  []
                                                      , RequestID   = self.__IncRequestID()
                                                      , ErrorID     = 0
                                                      , event       = threading.Event())
        ret = self.ReqQryInstrumentCommissionRate(QryInstrumentCommissionRate, self.__rsp_QryInstrumentCommissionRate['RequestID'])
        if ret == 0:
            self.__rsp_QryInstrumentCommissionRate['event'].clear()
            if self.__rsp_QryInstrumentCommissionRate['event'].wait(self.TIMEOUT):
                if self.__rsp_QryInstrumentCommissionRate['ErrorID'] != 0:
                    return self.__rsp_QryInstrumentCommissionRate['ErrorID']
                return self.__rsp_QryInstrumentCommissionRate['results']
            else:
                return -4
        return ret
    
    def QryInvestorPosition(self, InstrumentID=b''):
        """ 请求查询投资者持仓 """
        QryInvestorPositionFiel = dict(BrokerID=self.__BrokerID, InvestorID=self.__InvestorID, InstrumentID=InstrumentID)
        self.__rsp_QryInvestorPosition = dict(results=[], RequestID=self.__IncRequestID(), ErrorID=0, event=threading.Event())
        ret = self.ReqQryInvestorPosition(QryInvestorPositionFiel, self.__rsp_QryInvestorPosition['RequestID'])
        if ret == 0:
            self.__rsp_QryInvestorPosition['event'].clear()
            if self.__rsp_QryInvestorPosition['event'].wait(self.TIMEOUT):
                if self.__rsp_QryInvestorPosition['ErrorID'] != 0:
                    return self.__rsp_QryInvestorPosition['ErrorID']
                return self.__rsp_QryInvestorPosition['results']
            else:
                return -4
        return ret
        
    def QryTradingAccount(self):
        """ 请求查询资金账户 """
        QryTradingAccountField = dict(BrokerID=self.__BrokerID, InvestorID=self.__InvestorID)
        self.__rsp_QryTradingAccount = dict(results=[], RequestID=self.__IncRequestID(), ErrorID=0, event=threading.Event())
        ret = self.ReqQryTradingAccount(QryTradingAccountField, self.__rsp_QryTradingAccount['RequestID'])
        if ret == 0:
            self.__rsp_QryTradingAccount['event'].clear()
            if self.__rsp_QryTradingAccount['event'].wait(self.TIMEOUT):
                if self.__rsp_QryTradingAccount['ErrorID'] != 0:
                    return self.__rsp_QryTradingAccount['ErrorID']
                return self.__rsp_QryTradingAccount['results']
            else:
                return -4
        return ret
        
    def QryInvestor(self):
        """ 请求查询投资者 """
        InvestorField = dict(BrokerID=self.__BrokerID, InvestorID=self.__InvestorID)
        self.__rsp_QryInvestor = dict(results=[], RequestID=self.__IncRequestID(), ErrorID=0, event=threading.Event())
        ret = self.ReqQryInvestor(InvestorField, self.__rsp_QryInvestor['RequestID'])
        if ret == 0:
            self.__rsp_QryInvestor['event'].clear()
            if self.__rsp_QryInvestor['event'].wait(self.TIMEOUT):
                if self.__rsp_QryInvestor['ErrorID'] != 0:
                    return self.__rsp_QryInvestor['ErrorID']
                return self.__rsp_QryInvestor['results']
            else:
                return -4
        return ret
        
    def QryExchange(self, ExchangeID=b''):
        """ 请求查询交易所 """
        QryExchangeField = dict(ExchangeID=ExchangeID)
        self.__rsp_QryExchange = dict(results=[], RequestID=self.__IncRequestID(), ErrorID=0, event=threading.Event())
        ret = self.ReqQryExchange(QryExchangeField, self.__rsp_QryExchange['RequestID'])
        if ret == 0:
            self.__rsp_QryExchange['event'].clear()
            if self.__rsp_QryExchange['event'].wait(self.TIMEOUT):
                if self.__rsp_QryExchange['ErrorID'] != 0:
                    return self.__rsp_QryExchange['ErrorID']
                return self.__rsp_QryExchange['results']
            else:
                return -4
        return ret
        
    def QryDepthMarketData(self, InstrumentID):
        """ 请求查询行情 """
        QryDepthMarketData = dict(InstrumentID=InstrumentID)
        self.__rsp_QryDepthMarketData = dict(results=[], RequestID=self.__IncRequestID(), ErrorID=0, event=threading.Event())
        ret = self.ReqQryDepthMarketData(QryDepthMarketData, self.__rsp_QryDepthMarketData['RequestID'])
        if ret == 0:
            self.__rsp_QryDepthMarketData['event'].clear()
            if self.__rsp_QryDepthMarketData['event'].wait(self.TIMEOUT):
                if self.__rsp_QryDepthMarketData['ErrorID'] != 0:
                    return self.__rsp_QryDepthMarketData['ErrorID']
                return self.__rsp_QryDepthMarketData['results']
            else:
                return -4
        return ret
        
    def OrderInsert(self, InstrumentID, Action, Direction, Volume, Price, OrderPriceType=PyCTP.THOST_FTDC_OPT_LimitPrice):
        """ 开平仓(限价挂单)申报 """
        InputOrder = {}
        InputOrder['BrokerID'] = self.__BrokerID                            # 经纪公司代码
        InputOrder['InvestorID'] = self.__InvestorID                        # 投资者代码
        InputOrder['InstrumentID'] = InstrumentID                           # 合约代码
        InputOrder['OrderRef'] = self.__IncOrderRef()                       # 报单引用
        InputOrder['UserID'] = self.__UserID                                # 用户代码
        InputOrder['OrderPriceType'] = OrderPriceType      # 报单价格条件:限价
        InputOrder['Direction'] = Direction                                 # 买卖方向
        InputOrder['CombOffsetFlag'] = Action                               # 组合开平标志
        InputOrder['CombHedgeFlag']=PyCTP.THOST_FTDC_HF_Speculation         # 组合投机套保标志:投机
        InputOrder['LimitPrice'] = Price                                    # 价格
        InputOrder['VolumeTotalOriginal'] = Volume                          # 数量
        InputOrder['TimeCondition'] = PyCTP.THOST_FTDC_TC_GFD               # 有效期类型:当日有效
        InputOrder['VolumeCondition'] = PyCTP.THOST_FTDC_VC_AV              # 成交量类型:任意数量
        InputOrder['MinVolume'] = Volume                                    # 最小成交量
        InputOrder['ContingentCondition'] = PyCTP.THOST_FTDC_CC_Immediately # 触发条件:立即
        InputOrder['ForceCloseReason'] = PyCTP.THOST_FTDC_FCC_NotForceClose # 强平原因:非强平
        self.__rsp_OrderInsert = dict(FrontID=self.__FrontID
                                      , SessionID=self.__SessionID
                                      , InputOrder=InputOrder
                                      , RequestID=self.__IncRequestID()
                                      , event=threading.Event())
        ret = self.ReqOrderInsert(InputOrder, self.__rsp_OrderInsert['RequestID'])
        if ret == 0:
            self.__rsp_OrderInsert['event'].clear()
            if self.__rsp_OrderInsert['event'].wait(self.TIMEOUT):
                if self.__rsp_OrderInsert['ErrorID'] != 0:
                    sys.stderr.write(str(self.__rsp_OrderInsert['ErrorMsg'], encoding='gb2312'))
                    return self.__rsp_OrderInsert['ErrorID']
                return self.__rsp_OrderInsert.copy()
            else:
                return -4
        return ret
        
    
    def CancelOrderAction(self, OrderID, InstrumentID):
        """
         撤单，当前报单

        Args:
            OrderID (_type_): _description_
        """
        InputOrderAction = {}
        InputOrderAction['BrokerID'] = self.__BrokerID                            # 经纪公司代码
        InputOrderAction['InvestorID'] = self.__InvestorID                        # 投资者代码
        InputOrderAction['InstrumentID'] = InstrumentID                           # 合约代码
        InputOrderAction['OrderRef'] =    OrderID                                 # 报单引用
        InputOrderAction['UserID'] = self.__UserID                                # 用户代码
        InputOrderAction['ActionFlag'] = PyCTP.THOST_FTDC_AF_Delete               # 删除报单
        # OrderAction['OrderActionRef'] = 1
        
        self.__rsp_OrderAction = dict(FrontID=self.__FrontID
                                      , SessionID=self.__SessionID
                                      , InputOrder=InputOrderAction
                                      , RequestID=self.__IncRequestID()
                                      , event=threading.Event())
        ret = self.ReqOrderAction(InputOrderAction, self.__rsp_OrderAction['RequestID'])
        if ret == 0:
            self.__rsp_OrderAction['event'].clear()
            if self.__rsp_OrderAction['event'].wait(self.TIMEOUT):
                if self.__rsp_OrderAction['ErrorID'] != 0:
                    sys.stderr.write(str(self.__rsp_OrderAction['ErrorMsg'], encoding='gb2312'))
                    return self.__rsp_OrderAction['ErrorID']
                return self.__rsp_OrderAction.copy()
            else:
                return -4
        return ret
 
    def OnRspOrderAction(self, pInputOrderAction, RspInfo, RequestID, IsLast):
        """处理请求撤单请求"""
        print('OnRspOrderAction:', pInputOrderAction, RspInfo, RequestID, IsLast)
        if self.__rsp_OrderAction['RequestID'] == RequestID \
           and self.__rsp_OrderAction['InputOrder']['OrderRef'] == pInputOrderAction['OrderRef']:
            if RspInfo is not None and RspInfo['ErrorID'] != 0:
                self.__rsp_OrderAction.update(RspInfo)
                self.__rsp_OrderAction['event'].set()
                
    def QryOrder(self, InstrumentID, InsertTimeStart, InsertTimeEnd):
        # 	virtual int ReqQryOrder(CThostFtdcQryOrderField *pQryOrder, int nRequestID) = 0;
        QryOrderField = {}
        QryOrderField['BrokerID'] = self.__BrokerID                            # 经纪公司代码
        QryOrderField['InvestorID'] = self.__InvestorID                        # 投资者代码
        QryOrderField['InstrumentID'] = InstrumentID                           # 合约代码
        # TThostFtdcOrderSysIDType	OrderSysID;
        QryOrderField['InsertTimeStart'] = InsertTimeStart                         
        QryOrderField['InsertTimeEnd'] = InsertTimeEnd                         

        self.__rsp_QryAction = dict(FrontID=self.__FrontID
                                      , SessionID=self.__SessionID
                                      , InputOrder=QryOrderField
                                      , RequestID=self.__IncRequestID()
                                      , event=threading.Event())
        ret = self.ReqQryOrder(QryOrderField, self.__rsp_QryAction['RequestID'])
        if ret == 0:
            self.__rsp_QryAction['event'].clear()
            if self.__rsp_QryAction['event'].wait(self.TIMEOUT):
                if self.__rsp_QryAction['ErrorID'] != 0:
                    sys.stderr.write(str(self.__rsp_QryAction['ErrorMsg'], encoding='gb2312'))
                    return self.__rsp_QryAction['ErrorID']
                return self.__rsp_QryAction.copy()
            else:
                return -4
        return ret
        
    def OnRspQryOrder(self, pOrders, RspInfo, RequestID, IsLast):
        print('OnRspQryOrder:', pOrders, RspInfo, RequestID, IsLast)
        # todo save pOrders
        # __rsp_QryAction
        if self.__rsp_QryAction['RequestID'] == RequestID:
            if RspInfo is not None and RspInfo['ErrorID'] != 0:
                self.__rsp_QryAction.update(RspInfo)
                self.__rsp_QryAction['event'].set()
        
    
    def QryTrade(self, TradeID, TradeTimeStart, TradeTimeEnd):
        QryTradeField = {}
        QryTradeField['BrokerID'] = self.__BrokerID                            # 经纪公司代码
        QryTradeField['InvestorID'] = self.__InvestorID                        # 投资者代码
        QryTradeField['TradeID'] = TradeID                                     # 成交编号
        # TThostFtdcOrderSysIDType	OrderSysID;
        QryTradeField['TradeTimeStart'] = TradeTimeStart                         
        QryTradeField['TradeTimeEnd'] = TradeTimeEnd                         
        # ///投资单元代码
        # TThostFtdcInvestUnitIDType	InvestUnitID;
        # ///合约代码
        # TThostFtdcInstrumentIDType	InstrumentID;

        self.__rsp_QryTrade = dict(FrontID=self.__FrontID
                                      , SessionID=self.__SessionID
                                      , InputOrder=QryTradeField
                                      , RequestID=self.__IncRequestID()
                                      , event=threading.Event())
        ret = self.ReqQryTrade(QryTradeField, self.__rsp_QryTrade['RequestID'])
        if ret == 0:
            self.__rsp_QryTrade['event'].clear()
            if self.__rsp_QryTrade['event'].wait(self.TIMEOUT):
                if self.__rsp_QryTrade['ErrorID'] != 0:
                    sys.stderr.write(str(self.__rsp_QryTrade['ErrorMsg'], encoding='gb2312'))
                    return self.__rsp_QryTrade['ErrorID']
                return self.__rsp_QryTrade.copy()
            else:
                return -4
        return ret

        
    def OnRspQryTrade(self, pTrades, RspInfo, RequestID, IsLast):
        print('OnRspQryTrade:', pTrades, RspInfo, RequestID, IsLast)
        if self.__rsp_QryTrade['RequestID'] == RequestID:
            if RspInfo is not None and RspInfo['ErrorID'] != 0:
                self.__rsp_QryTrade.update(RspInfo)
                self.__rsp_QryTrade['event'].set()

    
    def OnFrontConnected(self):
        """ 当客户端与交易后台建立起通信连接时（还未登录前），该方法被调用。 """
        self.__rsp_Connect['event'].set()
    
    def OnFrontDisconnected(self, nReason):
        """ 当客户端与交易后台通信连接断开时，该方法被调用。当发生这个情况后，API会自动重新连接，客户端可不做处理。
        nReason 错误原因
        0x1001 网络读失败
        0x1002 网络写失败
        0x2001 接收心跳超时
        0x2002 发送心跳失败
        0x2003 收到错误报文        
        """
        sys.stderr.write('前置连接中断: %s' % hex(nReason))
        # 登陆状态时掉线, 自动重登陆
        #if self.__isLogined:
        #    self.__Inst_Interval()
        #    sys.stderr.write('自动登陆: %d' % self.Login(self.__BrokerID, self.__UserID, self.__Password))
        
    def OnRspUserLogin(self, RspUserLogin, RspInfo, RequestID, IsLast):
        """ 登录请求响应 """
        if RequestID == self.__rsp_Login['RequestID'] and IsLast:
            self.__BrokerID = RspUserLogin['BrokerID']
            self.__UserID = RspUserLogin['UserID']
            self.__SystemName = RspUserLogin['SystemName']
            self.__TradingDay = RspUserLogin['TradingDay']
            self.__DCETime = RspUserLogin['DCETime']
            self.__SessionID = RspUserLogin['SessionID'] 
            self.__MaxOrderRef = RspUserLogin['MaxOrderRef']
            self.__OrderRef = int(self.__MaxOrderRef) # 初始化报单引用
            self.__INETime = RspUserLogin['INETime']
            self.__LoginTime = RspUserLogin['LoginTime']
            self.__FrontID = RspUserLogin['FrontID']
            self.__FFEXTime = RspUserLogin['FFEXTime']
            self.__CZCETime = RspUserLogin['CZCETime']
            self.__SHFETime = RspUserLogin['SHFETime']
            self.__rsp_Login.update(RspInfo)
            self.__rsp_Login['event'].set()
            
    def OnRspUserLogout(self, RspUserLogout, RspInfo, RequestID, IsLast):
        """ 登出请求响应 """
        if RequestID == self.__rsp_Logout['RequestID'] and IsLast:
            self.__rsp_Logout.update(RspInfo)
            self.__rsp_Logout['event'].set()
            
    def OnRspAuthenticate(self, pRspAuthenticateField, RspInfo, RequestID, IsLast):
        """ 请求响应 """
        if RequestID == self.__rsp_Authenticate['RequestID'] and IsLast:
            self.__rsp_Authenticate.update(RspInfo)
            self.__rsp_Authenticate['event'].set()
            
    def OnRspQryInstrument(self, Instrument, RspInfo, RequestID, IsLast):
        """ 请求查询合约响应 """
        if RequestID == self.__rsp_QryInstrument['RequestID']:
            if RspInfo is not None:
                self.__rsp_QryInstrument.update(RspInfo)
            if Instrument is not None:
                self.__rsp_QryInstrument['results'].append(Instrument)
            if IsLast:
                self.__rsp_QryInstrument['event'].set()
                
    def OnRspQryInstrumentMarginRate(self, InstrumentMarginRate, RspInfo, RequestID, IsLast):
        """ 请求查询合约保证金率响应 """
        if RequestID == self.__rsp_QryInstrumentMarginRate['RequestID']:
            if RspInfo is not None:
                self.__rsp_QryInstrumentMarginRate.update(RspInfo)
            if InstrumentMarginRate is not None:
                self.__rsp_QryInstrumentMarginRate['results'].append(InstrumentMarginRate)
            if IsLast:
                self.__rsp_QryInstrumentMarginRate['event'].set()
                
    def OnRspQryInstrumentCommissionRate(self, InstrumentCommissionRate, RspInfo, RequestID, IsLast):
        """ 请求查询合约手续费率响应 """
        if RequestID == self.__rsp_QryInstrumentCommissionRate['RequestID']:
            if RspInfo is not None:
                self.__rsp_QryInstrumentCommissionRate.update(RspInfo)
            if InstrumentCommissionRate is not None:
                self.__rsp_QryInstrumentCommissionRate['results'].append(InstrumentCommissionRate)
            if IsLast:
                self.__rsp_QryInstrumentCommissionRate['event'].set()
                
    def OnRspQryInvestorPosition(self, InvestorPosition, RspInfo, RequestID, IsLast):
        """ 请求查询投资者持仓响应 """
        if RequestID == self.__rsp_QryInvestorPosition['RequestID']:
            if RspInfo is not None:
                self.__rsp_QryInvestorPosition.update(RspInfo)
            if InvestorPosition is not None:
                self.__rsp_QryInvestorPosition['results'].append(InvestorPosition)
            if IsLast:
                self.__rsp_QryInvestorPosition['event'].set()
                
    def OnRspQryTradingAccount(self, TradingAccount, RspInfo, RequestID, IsLast):
        """ 请求查询资金账户响应 """
        if RequestID == self.__rsp_QryTradingAccount['RequestID']:
            if RspInfo is not None:
                self.__rsp_QryTradingAccount.update(RspInfo)
            if TradingAccount is not None:
                self.__rsp_QryTradingAccount['results'].append(TradingAccount)
            if IsLast:
                self.__rsp_QryTradingAccount['event'].set()
                
    def OnRspQryInvestor(self, Investor, RspInfo, RequestID, IsLast):
        """ 请求查询投资者响应 """
        if RequestID == self.__rsp_QryInvestor['RequestID']:
            if RspInfo is not None:
                self.__rsp_QryInvestor.update(RspInfo)
            if Investor is not None:
                self.__rsp_QryInvestor['results'].append(Investor)
            if IsLast:
                self.__rsp_QryInvestor['event'].set()
    
    def OnRspQryExchange(self, Exchange, RspInfo, RequestID, IsLast):
        """ 请求查询交易所响应 """
        if RequestID == self.__rsp_QryExchange['RequestID']:
            if RspInfo is not None:
                self.__rsp_QryExchange.update(RspInfo)
            if Exchange is not None:
                self.__rsp_QryExchange['results'].append(Exchange)
            if IsLast:
                self.__rsp_QryExchange['event'].set()
                
    def OnRspQryDepthMarketData(self, DepthMarketData, RspInfo, RequestID, IsLast):
        """ 请求查询交易所响应 """
        if RequestID == self.__rsp_QryDepthMarketData['RequestID']:
            if RspInfo is not None:
                self.__rsp_QryDepthMarketData.update(RspInfo)
            if DepthMarketData is not None:
                self.__rsp_QryDepthMarketData['results'].append(DepthMarketData)
            if IsLast:
                self.__rsp_QryDepthMarketData['event'].set()
                
    def OnRspOrderInsert(self, InputOrder, RspInfo, RequestID, IsLast):
        """ 报单录入请求响应 """
        print('OnRspOrderInsert:', InputOrder, RspInfo, RequestID, IsLast)
        if self.__rsp_OrderInsert['RequestID'] == RequestID \
           and self.__rsp_OrderInsert['InputOrder']['OrderRef'] == InputOrder['OrderRef']:
            if RspInfo is not None and RspInfo['ErrorID'] != 0:
                self.__rsp_OrderInsert.update(RspInfo)
                self.__rsp_OrderInsert['event'].set()
                
    def OnRtnOrder(self, Order):
        print(Order)
        pass
    
    def OnErrRtnOrderAction(self, OrderAction, RspInfo):
        """ 报单操作错误回报 """
        print('OnErrRtnOrderAction:', OrderAction, RspInfo)
        #if not self.__rsp_OrderInsert['event'].is_set() and OrderAction['OrderActionStatus'] == PyCTP.THOST_FTDC_OST_Canceled:
        #    self.__rsp_OrderInsert['ErrorID'] = 79
        #    self.__rsp_OrderInsert['ErrorMsg'] = bytes('CTP:发送报单操作失败', 'gb2312')
        #    self.__rsp_OrderInsert['event'].set()

    def OnRtnTradingNotice(self, TradingNoticeInfo):
        """ 交易通知 """
        print('OnRtnTradingNotice:', TradingNoticeInfo)
        pass

class PyCTP_Trader(PyCTP_Trader_API):
    def OnRtnExecOrder(self, ExecOrder):
        print('OnRtnExecOrder:', ExecOrder)
        pass

class PyCTP_Market(PyCTP_Market_API):
    data = []
    def OnRtnDepthMarketData(self, DepthMarketData):
        import datetime
        tick = dict(InstrumentID=str(DepthMarketData['InstrumentID'], 'gb2312')
                    , time=datetime.datetime.strptime(str(DepthMarketData['ActionDay']+DepthMarketData['UpdateTime'], 'gb2312'), '%Y%m%d%H:%M:%S').replace(microsecond=DepthMarketData['UpdateMillisec']*1000)
                    , last=DepthMarketData['LastPrice']
                    , volume=DepthMarketData['Volume']
                    , amount=DepthMarketData['Turnover']
                    , position=DepthMarketData['OpenInterest']
                    , ask1=DepthMarketData['AskPrice1']
                    , bid1=DepthMarketData['BidPrice1']
                    , asize1=DepthMarketData['AskVolume1']
                    , bsize1=DepthMarketData['BidVolume1'])
        self.data.append(tick)
        print(tick, '\n')
    
def __main__():
    import os
    import time
    BrokerID = b''
    UserID = b''
    Password = b''
    AuthCode = b''
    AppID = b''
    ProductInfo = b''
    ExchangeID = b'SHFE'
    InstrumentID = b'cu1610'
    
    trader = PyCTP_Trader.CreateFtdcTraderApi(b'_tmp_t_')  
    market = PyCTP_Market.CreateFtdcMdApi(b'_tmp_m_')    
    print('连接前置', trader.Connect(b'tcp://x.x.x.x:x'))
    
    print('连接前置', market.Connect(b'tcp://x.x.x.x:x'))
    
    
    """
    1.直连模式
	2.中继服务器操作员模式(一对多模式)
	3.中继服务器非操作员模式(多对多模式)
    """
    mode_num  = 1
    if mode_num == 1:
        # 1.直连模式
        print('客户端认证', trader.Authenticate(BrokerID, UserID, ProductInfo, AuthCode, AppID))
        print('账号登陆', trader.Login(BrokerID, UserID, Password))
    elif mode_num == 2:
        # 2.中继服务器操作员模式(一对多模式)
        print('客户端认证', trader.Authenticate(BrokerID, UserID, ProductInfo, AuthCode, AppID))
        print('账号登陆', trader.Login(BrokerID, UserID, Password))
        print('上报用户终端信息', trader.SubUserSystemInfo(BrokerID, UserID, AppID))
    elif mode_num == 3:
        # 3.中继服务器非操作员模式(多对多模式)
        print('客户端认证', trader.Authenticate(BrokerID, UserID, ProductInfo, AuthCode, AppID))
        print('注册用户终端信息', trader.RegUserSystemInfo(BrokerID, UserID, AppID) )
        print('账号登陆', trader.Login(BrokerID, UserID, Password))
    else:
        print('选择的模式有误，请重新输入！')
      
    #print('账号登陆', market.Login(BrokerID, UserID, Password))
    
    print('投资者代码', trader.setInvestorID(UserID))    
    time.sleep(1.0)
    print('查询交易所', [(item['ExchangeID'], item['ExchangeName'].decode('gb2312'), item['ExchangeProperty']) for item in trader.QryExchange()])
    #time.sleep(1.0)
    #print('查询投资者', trader.QryInvestor())
    #time.sleep(1.0)
    #print('查询资金账户', trader.QryTradingAccount())
    #time.sleep(1.0)
    #print('查询合约', trader.QryInstrument(ExchangeID, InstrumentID))
    #time.sleep(1.0)
    #print('合约手续费率', trader.QryInstrumentCommissionRate(InstrumentID))
    #time.sleep(1.0)
    #print('合约保证金率', trader.QryInstrumentMarginRate(InstrumentID))
    #time.sleep(1.0)
    #print('投资者持仓', trader.QryInvestorPosition())
    #time.sleep(1.0)
    #print('查询行情', trader.QryDepthMarketData(InstrumentID))
    #time.sleep(1.0)
    #print('订阅行情:', market.SubMarketData([InstrumentID]))
    
    #while True:
    #    if input('enter q exit:') == 'q':
    #        break
    #time.sleep(1.0)
    #print('退订行情:', market.UnSubMarketData([InstrumentID]))
    #print('账号登出', trader.Logout())
    #print('账号登出', market.Logout())

if __name__ == '__main__':
    __main__()
