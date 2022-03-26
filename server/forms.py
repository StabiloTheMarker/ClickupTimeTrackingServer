import wtforms as forms

class GenerateReportForm(forms.Form):
    startdate = forms.DateField("Startdate")   
    enddate = forms.DateField("Enddate")  
    list_tasks = forms.BooleanField("List Tasks")
    export_pdf = forms.BooleanField("Export PDF")