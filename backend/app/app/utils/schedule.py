import logging
from rocketry import Rocketry

logger = logging.getLogger(__file__)


# Create Rocketry app
app = Rocketry(execution="async")

# Create some tasks
@app.task('every 5 seconds')
async def test_rocketry():
    logger.info("------rocketry run schedule-------")


if __name__ == "__main__":
    app.run()