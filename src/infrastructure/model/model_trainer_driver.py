from typing import Optional, Tuple

from core.entities.model.base_model_entity import BaseModelEntity

from ...core.entities.data.processed_data_entity import ProcessedDataEntity
from ...core.ports.model.model_trainer_port import ModelTrainer
from ...core.ports.logger_port import LoggerPort

from ...infrastructure.utils.common_util import custom_cosine_similarity, evaluate_embedding_model
from ...infrastructure.utils.data_wrapper_util import base_matrix_to_dataframe, dataframe_to_base_matrix
from ...infrastructure.utils.model_wrapper_util import base_model_to_keras_model

import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split

from keras.callbacks import EarlyStopping

class ModelTrainerDriver(ModelTrainer):
  def __init__(self, logger: LoggerPort) -> None:
    self.logger = logger
    
  
  def split_train_test_data(self, data: ProcessedDataEntity, test_ratio: int = 0.2) -> Tuple(ProcessedDataEntity, ProcessedDataEntity):
    df_data = base_matrix_to_dataframe(data)
    
    df_data_train, df_data_test = train_test_split(
      df_data,
      shuffle=True,
      stratify=df_data['label'],
      test_size=test_ratio,
      random_state=42)
    
    data_train, data_test = dataframe_to_base_matrix(df_data_train), dataframe_to_base_matrix(df_data_test)
    return (data_train, data_test)
  
  
  def train_model_training(self, model: BaseModelEntity, train_data: ProcessedDataEntity, valid_data: Optional[ProcessedDataEntity] = None) -> None:
    df_train_data = base_matrix_to_dataframe(train_data)
    df_valid_data = base_matrix_to_dataframe(valid_data)
    keras_model = base_model_to_keras_model(model)
    
    X_train, y_train = df_train_data.drop(columns=['label']), df_train_data['label']
    X_valid, y_valid = df_valid_data.drop(columns=['label']), df_valid_data['label']
    
    X_train_inputs = [np.vstack(X_train['text_embedded_left']), np.vstack(X_train['text_embedded_right'])]
    X_valid_inputs = [np.vstack(X_valid['text_embedded_left']), np.vstack(X_valid['text_embedded_right'])]
        
    early_stopping = EarlyStopping(monitor='loss', patience=5, restore_best_weights=True)
    epochs, batch_size = 10, 32
    
    keras_model.fit(
      X_train_inputs, y_train,
      epochs=epochs,
      batch_size=batch_size,
      validation_data=(X_valid_inputs, y_valid),
      callbacks=[early_stopping],
      verbose=0)
    
  def get_similarity_threshold(self, model: BaseModelEntity, data: ProcessedDataEntity) -> float:
    df_data = base_matrix_to_dataframe(data)
    keras_model = base_model_to_keras_model(model)
    
    thresholds = np.linspace(0, 1, 1000)

    embd_test_left = keras_model.predict(np.vstack(df_data['text_embedded_left']))
    embd_test_right = keras_model.predict(np.vstack(df_data['text_embedded_right']))
    similarity_scores = np.array([custom_cosine_similarity(embd_1, embd_2) for embd_1, embd_2 in zip(embd_test_left, embd_test_right)])
    
    threshold_eval = pd.DataFrame(
        [[threshold, *evaluate_embedding_model(similarity_scores, df_data['label'], threshold)] for threshold in thresholds],
        columns=['threshold', 'precision', 'recall', 'roc_auc']
      )
    max_threshold = threshold_eval.loc[threshold_eval['roc_auc'].argmax()]
    return max_threshold