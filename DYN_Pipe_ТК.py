import sys
import clr
clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager
clr.AddReference('RevitNodes')
import Revit
clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)

clr.AddReference('RevitAPI')
from Autodesk.Revit import DB

doc = DocumentManager.Instance.CurrentDBDocument
#uiapp = DocumentManager.Instance.CurrentUIApplication
#app = uiapp.Application
#uidoc = uiapp.ActiveUIDocument

#Входные данные
#Выделить начальный сегмент трубы в модели
el_id = IN[0].UniqueId
el = doc.GetElement(el_id)
#Выбрать параметр для записи нумерации в формате: "DYN_<Порядковый номер, начиная с 1>"
parameter = IN[1]
#Для отладки
log_1 = []
out_list = []
#Функция, очищающая значение выбранного параметра у всех труб
def clean():
    collector = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_PipeCurves).WhereElementIsNotElementType()
    for el in collector:
        el.LookupParameter(parameter).Set('')

#Функция распаковки Set для коннекторов в список
def unpacker(set):
    list = []
    for i in set:
        list.append(i)
    return(list)
#Функция, определяющая следующий сегмент трубы и записывающая порядковый номер ему в выбранный параметр
def next_conn(el, prev_el):
    #Счётчик
    i = 3
    #Марка:
    mark = 1
    #Для выбранного элемента:
    try:
        if el.Category.Name == "Трубы":
            if el.ConnectorManager!=None:
                #Сформировать список коннекторов для сегмента трубы (4 коннектора)
                conn_1 = unpacker(el.ConnectorManager.Connectors)
                conn_2 = [x for l in [unpacker(c1.AllRefs) for c1 in conn_1] for x in l]
                for conn in conn_2:
                    try:
                        if conn.GetMEPConnectorInfo().LinkedConnector:
                            #Если связанный коннектор для коннектора из списка ссылается на текущий элемент:
                            if unpacker(conn.GetMEPConnectorInfo().LinkedConnector.AllRefs)[0].Owner is el:
                                continue
                            #Если связанный коннектор для коннектора из списка ссылается на предыдущий элемент:
                            elif unpacker(conn.GetMEPConnectorInfo().LinkedConnector.AllRefs)[0].Owner is prev_el:
                                continue
                            #Если связанный коннектор для коннектора из списка не ссылается ни на предыдущий элемент, ни на текущий элемент:
                            elif unpacker(conn.GetMEPConnectorInfo().LinkedConnector.AllRefs)[0].Owner != prev_el:
                                segment_2 = unpacker(conn.GetMEPConnectorInfo().LinkedConnector.AllRefs)[0].Owner
                                log_1.append('Id следующего сегмента трубы:')
                                log_1.append(segment_2.Id)
                                el.LookupParameter(parameter).Set('DYN_1')
                                segment_2.LookupParameter(parameter).Set('DYN_2')
                                out_list.append(el)
                                out_list.append(segment_2)
                                #Присваием значения переменным, чтобы начать цикл:
                                prev_segment = el
                                segment = segment_2
                                mark = 2
                                break
                            else:
                                log_1.append('Ошибка! Id элемента:')
                                log_1.append(unpacker(conn.GetMEPConnectorInfo().LinkedConnector.AllRefs)[0].Owner.Id)
                                continue
                        else:
                            log_1.append('У коннектора нет связанного коннектора')
                            continue
                    except:
                        log_1.append('Неприсоединённый сегмент')
                        continue
            else:
                log_1.append('Выбранный элемент не присоединён в цепь')
                segment = None
        else:
            log_1.append('Выбранный элемент не принадлежит категории Трубы')
            segment = None
    except:
        log_1.append('Неправильно выбран начальный сегмент ветки трубы')
        segment = None

    #Цикл перебора:
    while segment:
        if mark:
            pass
        else:
            log_1.append('Выход из цикла')
            break
        #Если сегмент является категорией "Трубы":
        try:
            if segment.Category.Name == "Трубы":
                if segment.ConnectorManager!=None:
                    #Сформировать список коннекторов для сегмента трубы (4 коннектора)
                    s_conn_1 = unpacker(segment.ConnectorManager.Connectors)
                    s_conn_2 = [x for l in [unpacker(c1.AllRefs) for c1 in s_conn_1] for x in l]
                    for s_conn in s_conn_2:
                        try:
                            if s_conn.GetMEPConnectorInfo().LinkedConnector:
                                #Если связанный коннектор для коннектора из списка ссылается на текущий элемент:
                                if unpacker(s_conn.GetMEPConnectorInfo().LinkedConnector.AllRefs)[0].Owner.Id == segment.Id:
                                    log_1.append('Владелец связанного коннектора равен владельцу текущего сегмента')
                                    continue
                                #Если связанный коннектор для коннектора из списка ссылается на предыдущий элемент:
                                elif unpacker(s_conn.GetMEPConnectorInfo().LinkedConnector.AllRefs)[0].Owner.Id == prev_segment.Id:
                                    log_1.append('Владелец связанного коннектора равен владельцу предыдущего сегмента')
                                    continue
                                #Если связанный коннектор для коннектора из списка не ссылается ни на предыдущий элемент, ни на текущий элемент:
                                elif unpacker(s_conn.GetMEPConnectorInfo().LinkedConnector.AllRefs)[0].Owner.Id != prev_segment.Id:
                                    prev_segment = segment
                                    mis_segment = s_conn.Owner #пропускаемый элемент = категории "Соединительные детали"
                                    segment = unpacker(s_conn.GetMEPConnectorInfo().LinkedConnector.AllRefs)[0].Owner
                                    log_1.append('Id следующего сегмента трубы:')
                                    log_1.append(segment.Id)
                                    segment.LookupParameter(parameter).Set('DYN_'+str(i))
                                    out_list.append(segment)
                                    i+=1
                                    mark = i
                                    break
                                else:
                                    log_1.append('Ошибка! Id элемента:')
                                    log_1.append(unpacker(s_conn.GetMEPConnectorInfo().LinkedConnector.AllRefs)[0].Owner.Id)
                                    mark = None
                                    continue
                            else:
                                log_1.append('У коннектора нет связанного коннектора')
                                mark = None
                                continue
                        except:
                            log_1.append('Неприсоединённый сегмент')
                            mark = None
                            continue

                else:
                    log_1.append('Последний элемент не присоединён в цепь')
                    mark = None
                    break
            else:
                log_1.append('Последний элемент не принадлежит категории Трубы. Id предыдущего сегмента трубы:')
                log_1.append(prev_segment.Id)
                log_1.append('Id последнего элемента')
                log_1.append(segment.Id)
                log_1.append('Id предпоследнего элемента')
                log_1.append(mis_segment.Id)
                #Удаляем последний элемент в формируем списке сегментов труб, очищаем у последнего жлемента параметр для записи порядкового номера
                segment.LookupParameter(parameter).Set('')
                out_list.pop()

                try:
                    #Последний сегмент является Арматурой трубопроводов, Соединительной деталью или Оборудованием, нужно найти следующий сегмент категории Трубы и продолжить цикл перебора:
                    if segment.Category.Name == "Соединительные детали трубопроводов" or segment.Category.Name == "Арматура трубопроводов" or segment.Category.Name == "Оборудование":
                        log_1.append('Последний сегмент Соединительная деталь, Арматура или Оборудование')
                        if segment.MEPModel.ConnectorManager!=None:
                            #Сформировать список коннекторов для элемента (2 или более коннекторов)
                            f_conn_1 = unpacker(segment.MEPModel.ConnectorManager.Connectors)
                            f_conn_2 = [x for l in [unpacker(c1.AllRefs) for c1 in f_conn_1] for x in l]
                            for f_conn in f_conn_2:
                                try:
                                    if f_conn.GetMEPConnectorInfo().LinkedConnector:
                                        #Если связанный коннектор для коннектора из списка ссылается на текущий элемент:
                                        if unpacker(f_conn.GetMEPConnectorInfo().LinkedConnector.AllRefs)[0].Owner.Id == segment.Id:
                                            log_1.append('Владелец связанного коннектора равен владельцу текущего сегмента')
                                            continue
                                        #Если связанный коннектор для коннектора из списка ссылается на предыдущий элемент:
                                        elif unpacker(f_conn.GetMEPConnectorInfo().LinkedConnector.AllRefs)[0].Owner.Id == prev_segment.Id:
                                            log_1.append('Владелец связанного коннектора равен владельцу предыдущего сегмента')
                                            continue
                                        #Если связанный коннектор для коннектора из списка не ссылается ни на предыдущий элемент, ни на текущий элемент:
                                        elif unpacker(f_conn.GetMEPConnectorInfo().LinkedConnector.AllRefs)[0].Owner.Id != prev_segment.Id:
                                            prev_segment = segment
                                            segment = unpacker(f_conn.GetMEPConnectorInfo().LinkedConnector.AllRefs)[0].Owner
                                            log_1.append('Id следующего сегмента трубы:')
                                            log_1.append(segment.Id)
                                            if segment.Category.Name == "Трубы":
                                                segment.LookupParameter(parameter).Set('DYN_'+str(i-1))
                                                out_list.append(segment)
                                                mark = i-1
                                            break
                                        else:
                                            log_1.append('Ошибка! Id элемента:')
                                            log_1.append(unpacker(f_conn.GetMEPConnectorInfo().LinkedConnector.AllRefs)[0].Owner.Id)
                                            mark = None
                                            continue
                                    else:
                                        log_1.append('У коннектора нет связанного коннектора')
                                        mark = None
                                        continue
                                except:
                                    log_1.append('Неприсоединённый сегмент')
                                    mark = None
                                    continue

                        else:
                            log_1.append('Последний элемент не присоединён в цепь')
                            mark = None
                            break
                    else:
                        log_1.append('Последний сегмент ветки не опознан.Его категория:')
                        log_1.append(segment.Category.Name)
                        segment = None
                        break
                except:
                    log_1.append('Последний сегмент не обрабатывается. Рассоедините цепь перед эелементом с Id:')
                    log_1.append(segment.Id)
                    segment = None
                    break
                
            log_1.append('---___---___---')
        except:
            log_1.append('Сегмент не является категорией "Трубы"')
            segment = None
            break
#Закрытие активных транзакций
TransactionManager.Instance.ForceCloseTransaction()
#Выполнение транзакции
with DB.Transaction(doc) as t:
    t.Start('Пронумеровать сегменты ветки трубопровода')
    clean()
    next_conn(el, None)
    t.Commit()
#На выход подаётся список пронумерованных сегментов труб
OUT = out_list, log_1
