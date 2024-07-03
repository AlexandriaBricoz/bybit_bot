import yaml

form = yaml.safe_load(open('form.yml', 'r'))
print(form['deltaP']+1)