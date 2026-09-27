# -*- coding: utf-8 -*-
import re, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SRC = r"C:\Users\hardw\maistudy\transcripts\귀화면접_전체정리.txt"
raw = open(SRC, encoding="utf-8").read()

lines = [l.strip() for l in raw.splitlines()]
lines = [l for l in lines if l and not l.startswith("===") and not l.startswith("한국 귀화면접")]
flat = " ".join(lines)
flat = re.sub(r"\s+", " ", flat).strip()

SECTIONS = [
    (1, 57, "대한민국 개관 · 국호·국기·국가"),
    (58, 113, "한국사 1 · 고조선~조선 전기"),
    (114, 169, "한국사 2 · 조선 후기~근현대"),
    (170, 235, "헌법과 정치제도"),
    (236, 293, "정부 조직과 행정기관"),
    (294, 363, "사법제도와 생활법률"),
    (364, 420, "가족 호칭·명절·전통문화"),
    (421, 471, "전통예술·국토지리·사회보험"),
    (472, 547, "의료·교육·생활정보"),
]

def section_for(num):
    for lo, hi, title in SECTIONS:
        if lo <= num <= hi:
            return f"{lo}~{hi}", title
    return "?", "?"

marker_re = re.compile(r"(\d{1,3})\s*(?:번\s*[.,]?|\.)\s+")

# 1) find all candidate markers, keep only strictly-increasing subsequence 1..547
candidates = [(m.start(), m.end(), int(m.group(1))) for m in marker_re.finditer(flat)]
accepted = []
last_num = 0
for start, end, num in candidates:
    if num > last_num and num <= 547:
        accepted.append((start, end, num))
        last_num = num

print(f"accepted markers: {len(accepted)} / candidates: {len(candidates)}")

q_end_re = re.compile(r"(까요?(?!지)|\?|보세요|봅시다|보십시오)")

cards = []
for idx, (start, end, num) in enumerate(accepted):
    seg_end = accepted[idx + 1][0] if idx + 1 < len(accepted) else len(flat)
    segment = flat[end:seg_end].strip()

    m = q_end_re.search(segment)
    if m:
        question = segment[: m.end()].strip()
        # skip one immediate trailing punctuation char (., ?) after 까
        rest_start = m.end()
        while rest_start < len(segment) and segment[rest_start] in ".? ":
            if segment[rest_start] in ".?":
                rest_start += 1
                break
            rest_start += 1
        remainder = segment[rest_start:].strip()
        if not question.endswith(("?", ".")):
            question += "?"
    else:
        j = segment.find("다.")
        if j != -1:
            question = segment[: j + 2].strip()
            remainder = segment[j + 2 :].strip()
        else:
            question = segment.strip()
            remainder = ""

    answer = ""
    if remainder:
        m2 = re.search(r"다[.]?(?=\s|$)", remainder)
        if m2 and q_end_re.search(remainder[m2.end():]):
            # a further rephrased question follows -> cut here
            answer = remainder[: m2.end()].strip()
        else:
            # no further question signal -> whole remainder is one (possibly
            # multi-item enumerated) answer
            answer = remainder.strip()
        if answer and not answer.endswith("."):
            answer += "."

    qrange, title = section_for(num)
    cards.append({"n": num, "q": question, "a": answer, "sec": title, "range": qrange})

overrides = {
    539: {
        "q": "길을 가다가 우연히 봉투를 주었는데 그 봉투를 열어봤더니 500만원이 있습니다. 아무도 모르게 빨리 집에 가지고 갔습니다. 다음날부터 본인의 생활을 위해서 조금씩 돈을 사용합니다. 당신은 어떻게 생각합니까? 그리고 이 행동은 무엇이라고 합니까?",
        "a": "잘못된 행동입니다. 그리고 그 행동은 점유이탈물횡령이라고 합니다.",
    },
}
for c in cards:
    if c["n"] in overrides:
        c.update(overrides[c["n"]])

nums = [c["n"] for c in cards]
missing = [k for k in range(1, 548) if k not in nums]
empty_ans = [c["n"] for c in cards if not c["a"]]
print(f"cards: {len(cards)}  missing numbers: {missing}")
print(f"empty answers ({len(empty_ans)}): {empty_ans}")

out_path = r"C:\Users\hardw\AppData\Local\Temp\claude\C--Users-hardw-maistudy\c35999b1-3d86-45f6-aaef-04c39599ca64\scratchpad\qa_data.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(cards, f, ensure_ascii=False, indent=1)
print("wrote", out_path)
