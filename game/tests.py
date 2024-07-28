import time

from game.selenium_trends import SeleniumTrends

st = SeleniumTrends()
st.setup()

for i in range(10):
    start = time.time()
    st.get_data(['obama', 'biden'], 'US')
    print(f"time:{time.time() - start}")
