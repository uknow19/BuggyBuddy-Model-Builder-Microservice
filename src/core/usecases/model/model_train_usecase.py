from ....core.ports.model.model_trainer_port import ModelTrainer
from ....core.ports.model.model_evaluator_port import Model_Evaluator
from ....core.entities.model.base_model_entity import BaseModelEntity
from ....core.entities.data.processed_data_entity import ProcessedDataEntity

class ModelTrainUsecase:
  def __init__(
      self,
      model_trainer: ModelTrainer,
      model_evaluator: Model_Evaluator) -> None:
    self.model_trainer = model_trainer
    self.model_evaluator = model_evaluator
  
  
  def train_model_training(
      self,
      model_training: BaseModelEntity,
      model_embedding: BaseModelEntity,
      data: ProcessedDataEntity) -> None:
    train_data, valid_data = self.model_trainer.split_train_test_data(data, test_ratio=0.2)
    
    self.model_trainer.train_model_training(model_training, train_data=train_data, valid_data=valid_data)
    self.model_trainer.train_model_embedding(model_embedding, data=data)