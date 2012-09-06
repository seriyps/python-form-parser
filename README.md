python-form-parser
==================

Simple utilite/class for extract and fill HTML forms


Usage
------

    from lxml import etree
    from urllib import urlencode

    html_string = """
        <html>
            <body>
                <form action="my_path", method="POST" id="my_form">
                      <input type="text" name="my_field" value="my_value"/>
                      <input type="text" name="my_field2"/>
                      <input type="submit" name="my_submit" value="Submit the form"/>
                </form>
            </body>
        </html>
    """

    # parse and extract the form
    tree = etree.HTML(html_string)
    form = tree.xpath("//form[@id='my_form']")[0]

    # Extract default values and meta information
    ff = FormFiller(form)

    # click to 'my_submit' button: will return dictionary with all fields values
    form_data = ff.click('my_submit')
    print form_data
    {"my_field": "my_value",
     "my_submit": "Submit the form"}

    # fill user data
    form_data['some_name'] = 'some_value'

    # prefered way on how to fill user data:
    print ff.fill('my_submit', my_field2="my_value2")
    {"my_field": "my_value",
     "my_field2": "my_value2",
     "my_submit": "Submit the form"}

    # fields that not present on the original form are not allowed
    ff.fill('my_submit', field_not_present_in_form_name="my_value3")
    KeyError: 'Invalid form field'

    # prepare data for sending
    body = urlencode(form_data)
    url = ff.get_action_url("http://example.com/forms/my_form.html")
    print url
    'http://example.com/forms/my_path'  # my_path from form's "action" attribute
    method = ff.get_method()
    print method
    'POST'  # from form's "method" attr (GET is default)


TODO
----

Check that all form types are supported (eg, "file")