## To get the simulation results for each OD test and then we can get the percentage of OD tests detected, you need to follow the instructions below.
### decompress data.tar.gz and orders.tar.gz because data.tar.gz contains the file all-polluter-cleaner-info-combined.csv
all-polluter-cleaner-info-combined.csv contains all polluters and corresponding cleaners for all victims in our dataset
orders contains all the generated orders for four techniques
You need to apply the info from all-polluter-cleaner-info-combined.csv to simulate on orders.
all-polluter-cleaner-info-combined.csv is a huge file, but you can choose the lines related to one single module to simulate simply. We put a marine-polluter-cleaner-info-combined.csv under this directory.

The location to download data.tar.gz are on our website. The link is https://drive.google.com/file/d/1UYiJ2Ki2-oppV9VvRrmnOPEm5O6I2IL_ .
The location to download orders.tar.gz are also on out website. The link is https://drive.google.com/file/d/1DkjhitKbRK6X9iBvDh7ubLeWITi-Ybty .

### Then, you can run the following 
`python3 simulator.py ../../data/all-polluter-cleaner-info-combined.csv only`
`python3 simulator.py ../../data/all-polluter-cleaner-info-combined.csv intra`
`python3 simulator.py ../../data/all-polluter-cleaner-info-combined.csv inter`
`python3 simulator.py ../../data/all-polluter-cleaner-info-combined.csv static`

`python3 simulator.py ../../data/all-polluter-cleaner-info-combined.csv <name of method>`

### These scripts will automatically output to the screen to show for each module, what is the first order that can make each OD test pass and what is the first order that can make each OD test fail.
For example, if you want to get the minimal orders for intra-class on module marine-api. It will output like below.
`python3 simulator.py marine-polluter-cleaner-info-combined.csv intra`
slug,sha,module,OD test,have a passing order,the first passing order index,have a failing order,the first failing order index.
ktuukkan/marine-api,af00038,.,net.sf.marineapi.ais.event.AbstractAISMessageListenerTest.testBasicListenerWithUnexpectedMessage,True,0,True,9
ktuukkan/marine-api,af00038,.,net.sf.marineapi.ais.event.AbstractAISMessageListenerTest.testConstructor,True,0,True,9
ktuukkan/marine-api,af00038,.,net.sf.marineapi.ais.event.AbstractAISMessageListenerTest.testGenericsListenerDefaultConstructorThrows,True,0,True,9
ktuukkan/marine-api,af00038,.,net.sf.marineapi.ais.event.AbstractAISMessageListenerTest.testGenericsListener,True,0,True,9
ktuukkan/marine-api,af00038,.,net.sf.marineapi.ais.event.AbstractAISMessageListenerTest.testOnMessageWithExpectedMessage,True,0,True,9
ktuukkan/marine-api,af00038,.,net.sf.marineapi.ais.event.AbstractAISMessageListenerTest.testParametrizedConstructor,True,0,True,9
ktuukkan/marine-api,af00038,.,net.sf.marineapi.ais.event.AbstractAISMessageListenerTest.testSequenceListener,True,0,True,9
ktuukkan/marine-api,af00038,.,net.sf.marineapi.ais.event.AbstractAISMessageListenerTest.testSequenceListenerWithIncorrectOrder,True,0,True,9
ktuukkan/marine-api,af00038,.,net.sf.marineapi.ais.event.AbstractAISMessageListenerTest.testSequenceListenerWithMixedOrder,True,0,True,9
ktuukkan/marine-api,af00038,.,net.sf.marineapi.ais.parser.AISMessageFactoryTest.testCreate,True,0,True,9
ktuukkan/marine-api,af00038,.,net.sf.marineapi.ais.parser.AISMessageFactoryTest.testCreateWithIncorrectOrder,True,0,True,9
ktuukkan/marine-api,af00038,.,net.sf.marineapi.ais.parser.AISMessageFactoryTest.testCreateWithTwo,True,0,True,9

It looks like the above, it means for all OD tests in marine-api, orders/intra-orders/ktuukkan\_marine-api-.-af00038-intra-orders/order-0 is the first order that make these tests pass and orders/intra-orders/ktuukkan\_marine-api-.-af00038-intra-orders/order-9 is the first test that can make these tests fail.

Note that simulate for inter-class and Target Pairs algorithms requires a lot of time, we can only approximate on some orders like choose 1000 orders for Target Pairs algorithm.

## We also put the simulation results for all the OD tests in our dataset and for all four techniques in the files below.
only\_class\_simulation\_results.csv contains the simulation results for only-class algorithm.
intra\_class\_simulation\_results.csv contains the simulation results for intra-class algorithm.
inter\_class\_simulation\_results.csv contains the simulation results for inter-class algorithm.
staic\_class\_simulation\_results.csv contains the simulation results for Target Pairs algorithm.

