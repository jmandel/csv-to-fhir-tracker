from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, ElementNotVisibleException
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.webdriver.chrome.options import Options

import sys
import os
import argparse
import csv
import re
import json
import time


# disposition -> ballot resolution
# disposition comment or retract/withdarw -> resolution comment

validate_fields = {
 'On behalf of': (lambda c: c['On behalf of'], 'Real Submitter',None),
 'Submitted By': (lambda c: c['On behalf of'] or c['Submitted By'],'Real Submitter',None),
 'Comment grouping': (lambda c: c['Comment grouping'],'Group',None),
 'Resource(s)': (lambda c: c['Resource(s)'],'Resource(s)',None),
 'Ballot': (lambda c: c['Ballot'],'Specification',None),
 'Schedule': (lambda c: c['Schedule'],'Schedule',None),
 'HTML Page name(s)': (lambda c: c['HTML Page name(s)'],'HTML Page(s)',None),
 'Disposition WG': (lambda c: c['Disposition WG'],'Reviewing Work Group', None),
 'Disposition': (lambda c: c['Disposition'],'Ballot Resolution', None)
}

required_fields = ["Comment Number", "Summary", "URL", "Disposition Comment or Retract/Withdraw details"]

ballot_values = json.load(open("ballot_values.json"))

#  Manual tweaks
#  core: remote empty col R, remove \n from "Comment Number"

def log_note(note):
    print note
    old_log['notes'].append(note)

def read_comments(inputs):
    load_errors = []

    header = None
    ret = {}
    for one_input in inputs:
        slug = one_input['slug']
        one_csv = []
        with open(one_input['file'], 'rb') as csvfile:
            comment_reader =  csv.DictReader(csvfile)
            comments = list(comment_reader)
            if header == None:
                header = filter(lambda x: x, comment_reader.fieldnames)
            if header != filter(lambda x: x, comment_reader.fieldnames):
                print header
                print comment_reader.fieldnames
                for i in range(len(header)):
                    if header[i] !=  comment_reader.fieldnames[i]:
                        print "%s vs. %s"%(header[i], comment_reader.fieldnames[i])
                raise "Header mismatch in %s"%slug
            for c in comments:
                c['slug'] = slug
                for k in c:
                    if not k: continue
                    c[k] = c[k].strip().decode("utf-8")
                c["Summary"] = re.sub(r"\s+", " ", c["Summary"])
                c["URL"] = re.sub(r"\s+", " ", c["URL"])
                c["Section"] = re.sub(r"\s+", " ", c["Section"])
                ret[slug] = comments
                for k in required_fields:
                    if k not in c:
                        load_errors.append("%s - Can't find field %s"%(args.slug, k))

                for k,(extractor, v, mapper) in validate_fields.iteritems():
                    for found_val in re.split('\s*,\s*', extractor(c)):
                        if not found_val: continue
                        found_val = found_val.lower()
                        if found_val.lower() not in select_options[v]:
                            load_errors.append("%s - Can't find %s (col %s) in %s"%(
                                args.slug, found_val, k, v))
    #load_errors = set(load_errors)
    if load_errors:
        for e in load_errors:
            print "ERR: ", e.encode('ascii', 'ignore').decode('ascii')
        raise Exception("Load errors, aborting")
    print header

    return ret


def followup_comment(item):
    ret = """Vote: #%s - %s"""%(item["Comment Number"], item["Vote and Type"])

    if item["In person resolution requested"] :
        ret += "\nIn person: %s"%(item["In person resolution requested"])

    ret += issue_details(item)

    return ret

def issue_details(item):
    ret = ""

    if item["Submitted By"] != "" or item["Organization"] != "":
        org = item["Organization"]
        if org != "":
            org = "(%s)"%org
        ret += "\nSubmitted by: %s  %s"%(item["Submitted By"], org)

    if item["On behalf of"] != "" or item["Commenter Email"] != "":
        email = item["Commenter Email"]
        if email != "":
            email = "(%s)"%email
        ret += "\nOn behalf of: %s %s"%(item["On behalf of"], email)

    if item["Existing Wording"]:
        ret += "\nExisting Wording: %s"%item["Existing Wording"]

    if item["Proposed Wording"]:
        ret += "\nProposed Wording: %s"%item["Proposed Wording"]

    if item["Ballot Comment"]:
        ret += "\n---\nComment:\n%s"%(item["Ballot Comment"])

    if item["Summary"]:
        ret += "\n---\nSummary:\n%s"%(item["Summary"])


    return ret


def select_all(select_elt, values, field, item):
    for v in values:
        found = False
        for o in select_elt.options:
            if o.text.lower() == v.lower():
                select_elt._setSelected(o)
                found = True
        if not found:
            log_note("Value mismatch on %s/%s: field %s, couldn't find %s"%(
                item['slug'], item['Comment Number'], field, v))
    if len(select_elt.all_selected_options) > 1:
        select_elt.deselect_by_visible_text("None")

def select_box(label):
    label_elt = driver.find_element(By.XPATH, '//strong[text()="'+label+'"]')
    return Select(label_elt.find_element(By.XPATH, '../select'))

def input_box(label):
    label_elt = driver.find_element(By.XPATH, '//strong[text()="'+label+'"]')
    return label_elt.find_element(By.XPATH, '../input')

def input_iframediv(label):
    label_elt = driver.find_element(By.XPATH, '//strong[text()="'+label+'"]')
    return label_elt.find_element(By.XPATH, '../div')


def fill_iframe(divid, text):
    divid = divid.replace("[", "\[")
    divid = divid.replace("]", "\]")
    followup_iframe = WebDriverWait(driver, 5).until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "#"+divid+" iframe")))
    followup_box = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body[contenteditable='true']")))
    followup_box.clear()
    followup_box.send_keys(text)
    driver.switch_to_default_content()

def fill_followup(text):
    fill_iframe("cke_text_body", text)

def fill_details(text):
    fill_iframe("cke_details", text)

def save_changes():
    save_button = driver.find_element(By.PARTIAL_LINK_TEXT, 'Save changes')
    save_button.submit()
    WebDriverWait(driver, 10).until(EC.title_contains("Browse Tracker Item"))

def submit_item():
    add_button = driver.find_element(By.PARTIAL_LINK_TEXT, 'Add')
    add_button.submit()
    WebDriverWait(driver, 10).until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, "span.feedback"), "Successfully added"))
    feedback = driver.find_element(By.CSS_SELECTOR, "span.feedback")
    return re.findall("(\d+)",feedback.text)[0]

def set_disposition_status(item):
    if not item["Disposition Comment or Retract/Withdraw details"]:
        return
    mydiv = input_iframediv("Resolution")
    fill_iframe(mydiv.get_attribute('id') , item["Disposition Comment or Retract/Withdraw details"])

def set_disposition(item):
    if not item["Disposition"]:
        return
    resolution = select_box("Ballot Resolution")
    select_all(resolution, [item["Disposition"]], "Disposition", item)

def set_ballot_weight(item):
    ballot_weight = select_box("Ballot-weight")
    current_selection = ballot_weight.all_selected_options[0].text
    desired_selection = item['Vote and Type']
    label = None
    if desired_selection.startswith("A") and current_selection.startswith("None"):
        label = "Affirmative"
    elif desired_selection.endswith("Mi") and not current_selection.endswith("Major"):
        label = "Negative-Minor"
    elif desired_selection.endswith("Mj") or desired_selection == "NEG":
        label = "Negative-Major"

    if label:
        ballot_weight.select_by_visible_text(label)

def set_in_person(item):
    in_person = select_box("In-Person?")
    current_selection = in_person.all_selected_options[0].text
    in_person_desired = item["In person resolution requested"] == "Yes"
    if in_person_desired and not current_selection.startswith("Yes"):
         in_person.select_by_visible_text("Yes")

def set_workgroup(item):
    if not item['Disposition WG']:
        return
    workgroup = select_box("Reviewing Work Group")
    desired_selections = item['Disposition WG']
    desired_selections = re.split('\s*,\s*', desired_selections)
    ss = []
    for s in desired_selections:
        ss.append(s.lower())
    select_all(workgroup, ss, "Workgroup", item)

def set_resource_and_pages(item):
    if item["Resource(s)"]:
        rs = item["Resource(s)"]
        rs = re.split('\W+', rs)
        select_all(select_box("Resource(s)"), rs, "Resource(s)", item)

    if item["HTML Page name(s)"]:
        select_all(select_box("HTML Page(s)"), [
                    s.lower() for s in re.split('\s*,\s*', item["HTML Page name(s)"])
                ], "HTML Page name(s)", item)


def set_specification(item):
    if item["Ballot"]:
        s = item["Ballot"]
        select_all(select_box("Specification"),[s], "Ballot", item)

def set_submitter(item):
    submitter = item["On behalf of"] or item["Submitted By"]
    if submitter:
        select_all(select_box("Real Submitter"),[submitter], "On behalf of", item)


def set_url(item):
    if item["URL"]:
        urlbox = input_box("url")
        urlbox.clear()
        urlbox.send_keys(item["URL"])

def navigate_to(url, form):
    driver.get(url)
    element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, form)))

def navigate_to_edit(item_id):
    navigate_to(edit_url%item_id, "TrackerItemEdit")


def navigate_to_add(tracker_id):
    navigate_to(add_url%tracker_id, "TrackerItemAdd")

def update_tracker_item(item):
    navigate_to_edit(item['Tracker #'])
    set_ballot_weight(item)
    set_in_person(item)
    set_workgroup(item)
    set_url(item)
    set_resource_and_pages(item)
    fill_followup(followup_comment(item))
    select_all(select_box("Ballot"),[ballot_values[args.slug]], "Ballot", item)

    current_spec = select_box("Specification").all_selected_options[0].text
    if (current_spec != item["Ballot"]):
        log_note("Specification mismatch: %s/%s: Tracker item %s has %s instead of %s"%(item['slug'],
                                                                             item['Comment Number'],
                                                                             item['Tracker #'],
                                                                             current_spec,
                                                                             item['Ballot']))
    save_changes()
    return item['Tracker #']

def create_tracker_item(item):
    navigate_to_add(tracker_id)
    summary_val = ""
    if item["Summary"]:
        summary_val += "%s - "%item["Summary"]
    summary_val += "%s #%s "%(item['slug'], item["Comment Number"])
    summary_field = driver.find_element(By.NAME, "summary")
    summary_field.send_keys(summary_val)

    if item["Section"]:
        input_box("Section number").send_keys(item["Section"])

    set_resource_and_pages(item)

    fill_details(issue_details(item))
    new_item_id = submit_item()

    navigate_to_edit(new_item_id)
    select_all(select_box("Status"), ["Triaged"], "Status", item)
    set_ballot_weight(item)
    set_workgroup(item)
    set_submitter(item)
    set_disposition(item)
    set_disposition_status(item)
    set_url(item)
    select_all(select_box("Ballot"),[ballot_values[args.slug]], "Ballot", item)
    category = item["Sub-category"]
    vote = item["Vote and Type"]
    if not category:
        if vote == "A-T": category = "Typo"
        elif vote == "A-Q": category = "Question"
        elif vote == "A-S": category = "Comment"
        elif vote == "A-C": category = "Comment"
    if category:
        select_all(select_box("Category"), [category], "Category", item)
    else:
        log_note("Invalid Category for %s: '%s'"%(summary_val, category))

    set_specification(item)
    set_in_person(item)
    if item["Comment grouping"]:
        select_all(select_box("Group"), [item["Comment grouping"]], "Group", item)

    if item["Triage Note"]:
        fill_followup("Triaged: %s"%item["Triage Note"])

    if item["Schedule"]:
        select_all(select_box("Schedule"), [item["Schedule"]], "Schedule", item)
    save_changes()
    return new_item_id

def load_one_spreadsheet(slug, comments, creates=True, updates=True):

    outcomes = {
      'creates': [],
      'updates': []
    }

    print "Loading spreadsheet", slug

    for item in comments:
        comment_id = "%s/%s"%(slug, item["Comment Number"])
        if comment_id in old_log['completed']:
            print "Skipping completed comment: %s" % comment_id
            continue
        print "Handling comment: %s"%comment_id
        if item['Tracker #']:
            if updates:
                result = update_tracker_item(item)
                outcomes['updates'].append(result)
                log_note("... updated %s as tracker #%s"%(comment_id, result))
                old_log['completed'].append(comment_id)

        else:
            if creates:
                result = create_tracker_item(item)
                outcomes['creates'].append(result)
                log_note("... created %s as tracker #%s"%(comment_id, result))
                old_log['completed'].append(comment_id)


    return outcomes



# Manually navigate to any "edit" page
def regenerate_select_validators():
    print "regenerating select options"
    selects = driver.find_elements(By.CSS_SELECTOR, "select")
    select_options = {}
    for s in selects:
        sel = Select(s)
        options = [o.text.lower() for o in sel.options]
        try:
            k =s.find_element(By.XPATH, '../strong').text
            if k != "":
                select_options[k] =  options
        except: pass
    return select_options

def login():
    username = os.getenv('GFORGE_USERNAME')
    password = os.getenv('GFORGE_PASSWORD')
    print("u", username)
    driver.get("http://gforge.hl7.org/gf/account/?action=Login")
    username_box = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='username']")))
    password_box = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
    username_box.clear()
    username_box.send_keys(username)
    password_box.clear()
    password_box.send_keys(password)
    login_button = driver.find_element(By.CSS_SELECTOR, "div.button a")
    login_button.submit()

parser = argparse.ArgumentParser(description='Handle FHIR Ballot issues', epilog='This program requires that chromedriver is running in the background (port 9515), and that environment variables GFORGE_USERNAME and GFORGE_PASSWORD are present.')

parser.add_argument('--tracker', help='GForge tracker id to write new items to')
parser.add_argument('--csvfile', help='csv file to process')
parser.add_argument('--logfile', nargs='?', default='progress.log.json', help='file to log progress for resume-after-error')
parser.add_argument('--slug', help='short name or "slug" to use in referring to this CSV file')
parser.add_argument('--do-updates', action='store_true', help='perform updates on issues that have existing tracker items')
parser.add_argument('--do-creates', action='store_true', help='perform creates on issues that have no existing tracker items')

parser.add_argument('--generate-select-options', action='store_true', help='regenerate select options from a known FHIR ballot issue')

if len(sys.argv)==1:
    parser.print_help()
    sys.exit(1)

args = parser.parse_args()
print args

tracker_id = args.tracker
edit_url = "http://gforge.hl7.org/gf/project/fhir/tracker/?action=TrackerItemEdit&tracker_item_id=%s"
add_url = "http://gforge.hl7.org/gf/project/fhir/tracker/?action=TrackerItemAdd&tracker_id=%s"

if args.generate_select_options:
    driver = webdriver.Remote("http://localhost:9515", {})
    login()
    navigate_to_edit("10000")
    select_options = regenerate_select_validators()
    options = open("select_options.json", "w")
    options.write(json.dumps(select_options, indent=2))
    options.close()
    sys.exit(0)

select_options = json.load(open("select_options.json"))

old_log = {'completed': [], 'notes': []}
try:
    with open(args.logfile) as input_log:
        old_log = json.load(input_log)
except: pass

if args.slug not in ballot_values:
    print("ERR: %s - not present in Ballot values"%args.slug)

input_comments = read_comments([{'slug': args.slug, 'file': args.csvfile}])[args.slug]
if not (args.do_creates or args.do_updates):
    print("No work to do -- just validated.")
    sys.exit(0)

driver = webdriver.Remote("http://localhost:9515", {})
try:
    login()
    load_one_spreadsheet(args.slug, input_comments, creates=args.do_creates, updates=args.do_updates)
finally:
    with open(args.logfile, "w") as output_log:
        json.dump(old_log, output_log, indent=2)

