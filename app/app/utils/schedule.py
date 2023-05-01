import logging
from rocketry import Rocketry

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__file__)


# Create Rocketry app
app = Rocketry(execution="async")


# Create a task
@app.task("every 5 seconds")
async def test_rocketry():
    logger.info("------rocketry run schedule-------")


if __name__ == "__main__":
    app.run()
