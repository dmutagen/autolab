import os
import zipfile
import xml.etree.ElementTree as ET
import json
import re

base_dir = '/home/mugo/Documents/ЛАБЫ_ПРАКТОСЫ'
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

kb = {
    'institutions': set(),
    'specialties': set(),
    'groups': set(),
    'students': set(),
    'teachers': set(),
    'subjects': {},
    'examples': [],
    'conclusions': [],
    'equipments': set()
}

def extract_from_docx(path):
    try:
        with zipfile.ZipFile(path) as z:
            if 'word/document.xml' not in z.namelist():
                return None
            tree = ET.fromstring(z.read('word/document.xml'))
            paras = []
            for p in tree.findall('.//w:p', ns):
                text = ''.join(p.itertext()).strip()
                if text:
                    paras.append(text)
            return paras
    except Exception:
        return None

count = 0
for root, dirs, files in os.walk(base_dir):
    for f in files:
        if f.endswith('.docx') and not f.startswith('~$'):
            full_path = os.path.join(root, f)
            paras = extract_from_docx(full_path)
            if not paras:
                continue
            count += 1
            rel = os.path.relpath(full_path, base_dir)
            category = rel.split(os.sep)[0]
            
            lab_no = None
            theme = None
            goal = None
            task = None
            equip = None
            conclusion = None
            
            for p in paras:
                m_lab = re.search(r'(Лабораторная|Практическая)\s+работа\s*№?\s*([0-9]+[\.\d]*)', p, re.I)
                if m_lab and not lab_no:
                    lab_no = m_lab.group(0)
                m_grp = re.search(r'группы:?\s*([А-Яа-яA-Za-z0-9\-]+)', p, re.I)
                if m_grp:
                    kb['groups'].add(m_grp.group(1).strip())
                m_fio = re.search(r'(?:обучающегося|студента|Фамилия, инициалы|Выполнил):?\s*([А-ЯЁ][а-яё]+ [А-ЯЁ]\.[А-ЯЁ]\.?|[А-ЯЁ]\.[А-ЯЁ]\.?\s*[А-ЯЁ][а-яё]+)', p, re.I)
                if m_fio:
                    kb['students'].add(m_fio.group(1).strip())
                m_theme = re.search(r'Тема(?:\s*работы)?:?\s*[«\"]?(.*?)[»\"]?$', p, re.I)
                if m_theme and not theme and len(m_theme.group(1)) > 3:
                    theme = m_theme.group(1).strip('«»" ')
                m_goal = re.search(r'Цель(?:\s*работы)?:?\s*(.*)', p, re.I)
                if m_goal and not goal:
                    goal = m_goal.group(1).strip()
                m_equip = re.search(r'Оснащение(?:\s*работ[ыа]?)?:?\s*(.*)', p, re.I)
                if m_equip:
                    kb['equipments'].add(m_equip.group(1).strip())
                m_concl = re.search(r'Вывод:?\s*(.*)', p, re.I)
                if m_concl:
                    concl_text = m_concl.group(1).strip()
                    if concl_text:
                        kb['conclusions'].append(concl_text)
            
            if theme or goal:
                kb['examples'].append({
                    'file': rel,
                    'category': category,
                    'lab': lab_no,
                    'theme': theme,
                    'goal': goal
                })

print(f'Processed {count} docx files.')
print('Groups:', sorted(list(kb['groups'])))
print('Students:', sorted(list(kb['students'])))
print(f'Conclusions collected: {len(kb["conclusions"])}')
print(f'Examples collected: {len(kb["examples"])}')

kb_serializable = {
    'default_institution': 'Учреждение образования «Гомельский государственный машиностроительный колледж»',
    'default_specialty': '5-04-0611-01 «Программирование мобильных устройств»',
    'default_group': 'ПМ-31',
    'default_student': 'Кашевич Е.Н.',
    'default_city': 'Гомель',
    'default_year': '2026',
    'groups': sorted(list(kb['groups'])),
    'students': sorted(list(kb['students'])),
    'equipments': sorted(list(kb['equipments']))[:20],
    'sample_conclusions': kb['conclusions'][:30],
    'examples': kb['examples']
}

with open('/home/mugo/autolab-ai/knowledge_base.json', 'w', encoding='utf-8') as out:
    json.dump(kb_serializable, out, ensure_ascii=False, indent=2)

print('Saved knowledge_base.json successfully!')
