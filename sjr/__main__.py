from sjr.jenkins import Jenkins

j = Jenkins()
j.build("client-tests", {})
j.debug()
