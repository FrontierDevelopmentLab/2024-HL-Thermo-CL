import sys
sys.path.append('../')
import pandas as pd
import karman
import torch
from omegaconf import OmegaConf
from tft_torch import tft
import tft_torch.loss as tft_loss
import torch.nn.init as init
import numpy as np
import wandb
from pyfiglet import Figlet
from termcolor import colored
from tqdm import tqdm
import argparse
import pprint
import time
from torch import optim
from torch.utils.data import RandomSampler, SequentialSampler
import random

def mean_absolute_percentage_error(y_pred,y_true):
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

def mse(y_pred,y_true):
    return np.mean((y_true - y_pred) ** 2)

def seed_worker(worker_id):
    worker_seed = torch.initial_seed() % 2**32
    np.random.seed(worker_seed)
    random.seed(worker_seed)

def train():
    print('Karman Model Training -> Forecasting the density of the atmosphere')
    f = Figlet(font='5lineoblique')
    print(colored(f.renderText('KARMAN 2.0'), 'red'))
    f = Figlet(font='digital')
    print(colored(f.renderText("Training Forecasting Model"), 'blue'))
    print(colored(f'Version {karman.__version__}\n','blue'))
    parser = argparse.ArgumentParser(description='HL-24 Karman Model Training', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--device', type=str, default='cpu', help='Device to use for training')
    parser.add_argument('--torch_type', type=str, default='float32', help='Torch type to use for training')
    parser.add_argument('--batch_size', type=int, default=64, help='Batch size for training')
    parser.add_argument('--normalization_dict_path', type=str, default=None, help='Path to the normalization dictionary. If None, the normalization values are computed on the fly')
    parser.add_argument('--model_path', type=str, default=None, help='Path to the model to load. If None, a new model is created')
    parser.add_argument('--lr', type=float, default=0.001, help='Learning rate for the optimizer')
    parser.add_argument('--run_name', default='', help='Run name to be stored in wandb')
    parser.add_argument('--thermo_path', default='../data/satellites_data_w_sw_2mln.csv', help='Path to the thermo dataset. Default is ../data/satellites_data_w_sw.csv')
    parser.add_argument('--epochs', type=int, default=5, help='Number of epochs to train the model')
    parser.add_argument('--num_workers', type=int, default=0, help='Number of workers for the dataloader')
    parser.add_argument('--min_date', type=str, default='2000-07-29 00:59:47', help='Min date to consider for the dataset')
    parser.add_argument('--max_date', type=str, default='2024-05-31 23:59:32', help='Max date to consider for the dataset')
    #parser.add_argument('--hidden_layer_dim', type=int, default=48, help='Hidden layer dimension')
    #parser.add_argument('--hidden_layers', type=int, default=3, help='Number of hidden layers')
    #parser.add_argument('--train_type', type=str, default='log_exp_residual', choices= ['log_density', 'log_exp_residual'], help='Training type, currently supports either log_density or log_exp_residual')
    parser.add_argument('--omni_indices_path', type=str, default='../data/omniweb_data/merged_omni_indices.csv', help='Path to the omni indices dataset')
    parser.add_argument('--omni_magnetic_field_path', type=str, default='../data/omniweb_data/merged_omni_magnetic_field.csv', help='Path to the omni magnetic field dataset')
    parser.add_argument('--omni_solar_wind_path', type=str, default='../data/omniweb_data/merged_omni_solar_wind.csv', help='Path to the omni solar wind dataset')
    parser.add_argument('--nrlmsise00_path', type=str, default='../data/nrlmsise00_data/nrlmsise00_time_series.csv', help='Path to the nrlmsise00 dataset')
    parser.add_argument('--goes_path', type=str, default=None, help='Path to the goes dataset')
    parser.add_argument('--soho_path', type=str, default='../data/soho_data/soho_data.csv', help='Path to the soho dataset')
    parser.add_argument('--lag_minutes', type=int, default=500, help='Lag in minutes for the time series datasets, default is 500 minutes')
    parser.add_argument('--resolution_minutes', type=int, default=10, help='Resolution for the time series datasets, default is 10 minutes')
    parser.add_argument('--dropout', type=float, default=0.05, help='Dropout rate for the TFT model')
    parser.add_argument('--state_size', type=int, default=64, help='State size for the TFT model')
    parser.add_argument('--lstm_layers', type=int, default=2, help='Number of LSTM layers of the TFT')
    parser.add_argument('--attention_heads', type=int, default=4, help='Number of attention heads for the TFT')
    parser.add_argument('--wandb_inactive', action='store_true', help='Flag to activate/deactivate weights and biases')
    #parser.add_argument('--no-wandb_active', dest='wandb_active', action='store_false', help='Flag to activate/deactivate weights and biases')
    parser.add_argument('--features_to_exclude_thermo', type=str, default='', help='Comma-separated features to exclude from the thermo dataset, besides the ones that are already excluded by default (see default in the KarmanDataset class)')
    #celestrack__ap_average__,JB08__d_st_dt__[K],space_environment_technologies__f107_obs__,space_environment_technologies__f107_average__,space_environment_technologies__s107_obs__,space_environment_technologies__s107_average__,space_environment_technologies__m107_obs__,space_environment_technologies__m107_average__,space_environment_technologies__y107_obs__,space_environment_technologies__y107_average__
    opt = parser.parse_args()

    if opt.nrlmsise00_path=='None':
        raise ValueError('NRLMSISE-00 path must be provided')

    if opt.wandb_inactive == False:
        wandb.init(project='karman', group='tft', config=vars(opt))
        # wandb.init(mode="disabled")
        if opt.run_name != '':
            wandb.run.name = opt.run_name
            wandb.run.save()
    print('Arguments:\n{}\n'.format(' '.join(sys.argv[1:])))
    print('Config:')
    pprint.pprint(vars(opt), depth=2, width=1)
    print()


    if 'float32':
        torch_type=torch.float32
    elif 'float64':
        torch_type=torch.float64
    else:
        raise ValueError('Invalid torch type. Only float32 and float64 are supported')
    torch.set_default_dtype(torch_type)
    features_to_exclude_thermo=["all__dates_datetime__", "tudelft_thermo__satellite__", "tudelft_thermo__ground_truth_thermospheric_density__[kg/m**3]", "all__year__[y]", "NRLMSISE00__thermospheric_density__[kg/m**3]"]
    if opt.features_to_exclude_thermo!='':    
        features_to_exclude_thermo+=opt.features_to_exclude_thermo.split(',')
    karman_dataset=karman.KarmanDataset(thermo_path=opt.thermo_path,
                                        min_date=pd.to_datetime(opt.min_date),
                                        max_date=pd.to_datetime(opt.max_date),
                                        normalization_dict=None,
                                        nrlmsise00_path=[None if opt.nrlmsise00_path=='None' else opt.nrlmsise00_path][0],
                                        omni_indices_path=[None if opt.omni_indices_path=='None' else opt.omni_indices_path][0],
                                        omni_magnetic_field_path=[None if opt.omni_magnetic_field_path=='None' else opt.omni_magnetic_field_path][0],
                                        omni_solar_wind_path=[None if opt.omni_solar_wind_path=='None' else opt.omni_solar_wind_path][0],
                                        soho_path=[None if opt.soho_path=='None' else opt.soho_path][0],
                                        lag_minutes_nrlmsise00=opt.lag_minutes,
                                        nrlmsise00_resolution=opt.resolution_minutes,
                                        lag_minutes_omni=opt.lag_minutes,
                                        omni_resolution=opt.resolution_minutes,
                                        lag_minutes_soho=opt.lag_minutes,
                                        soho_resolution=opt.resolution_minutes,
                                        features_to_exclude_thermo=features_to_exclude_thermo
                            )
    input_dimension=karman_dataset[0]['instantaneous_features'].shape[0]
    if opt.device.startswith('cuda'):
        device = torch.device(opt.device if torch.cuda.is_available() else 'cpu')
    else:
        device=torch.device('cpu')    
    print(f'Device is {device}')
    
    # set configuration
    num_historical_numeric=0
    
    if opt.omni_indices_path != 'None':
        num_historical_numeric+=karman_dataset[0]['omni_indices'].shape[1]
    if opt.omni_magnetic_field_path!='None':
        num_historical_numeric+=karman_dataset[0]['omni_magnetic_field'].shape[1]
    if opt.omni_solar_wind_path!='None':
        num_historical_numeric+=karman_dataset[0]['omni_solar_wind'].shape[1]
    if opt.nrlmsise00_path!='None':
        num_historical_numeric+=karman_dataset[0]['msise'].shape[1]
    if opt.soho_path!='None':
        num_historical_numeric+=karman_dataset[0]['soho'].shape[1]
#    if opt.goes_path is not None:
#        raise NotImplementedError('GOES dataset not implemented yet')
    
    if num_historical_numeric==0:
        raise ValueError('No historical numeric data found in the dataset')
    
    data_props = {'num_historical_numeric': num_historical_numeric,
                'num_static_numeric': input_dimension,
                'num_future_numeric': 1,
                }

    configuration = {
                    'model':
                        {
                            'dropout': opt.dropout,
                            'state_size': opt.state_size,
                            'output_quantiles': [0.5],
                            'lstm_layers': opt.lstm_layers,
                            'attention_heads': opt.attention_heads,
                        },
                    'task_type': 'regression',
                    'target_window_start': None,
                    'data_props': data_props,
                    }

    # initialize tft_model
    tft_model = tft.TemporalFusionTransformer(OmegaConf.create(configuration))
    # weight init
    tft_model.apply(karman.nn.weight_init)
    tft_model.to(device)
    
    #if the model path is passed, load from there:
    if opt.model_path is not None:
        tft_model.load_state_dict(torch.load(opt.model_path))

    num_params=sum(p.numel() for p in tft_model.parameters() if p.requires_grad)
    print(f'Karman model num parameters: {num_params}')
    
    # create batch as an example
    historical_steps = karman_dataset[0]['msise'].shape[0]-1
    future_steps = 1

    #Train, validation, test splits:
    idx_test_fold=2
    test_month_idx = 2 * (idx_test_fold - 1)
    validation_month_idx = test_month_idx + 2
    print(test_month_idx,validation_month_idx)
    karman_dataset._set_indices(test_month_idx=[test_month_idx], validation_month_idx=[validation_month_idx],custom={2001: {"validation":2,"test":3},
                                                                                                                     2003: {"validation":9, "test":10},
                                                                                                                     2005: {"validation":4, "test":5},
                                                                                                                     2012: {"validation":8, "test":9},
                                                                                                                     2013: {"validation":4, "test":5},
                                                                                                                     2015: {"validation":2, "test":3},
                                                                                                                     2022: {"validation":0, "test":1},
                                                                                                                     2024: {"validation":3,"test":4}})
    train_dataset = karman_dataset.train_dataset()
    validation_dataset = karman_dataset.validation_dataset()
    test_dataset = karman_dataset.test_dataset()
    print(f'Training dataset example: {train_dataset[0].items()}')

    train_sampler = RandomSampler(train_dataset, num_samples=len(train_dataset))
    validation_sampler = RandomSampler(validation_dataset, num_samples=len(validation_dataset))
    test_sampler = SequentialSampler(test_dataset)

    ####### Training Parameters ##########
    # Here we set the optimizer
    #optimizer:
    optimizer = optim.Adam(
        filter(lambda p: p.requires_grad, list(tft_model.parameters())),
        lr=opt.lr,
        amsgrad=True,
    )
    #scheduler = torch.optim.lr_scheduler.MultiStepLR(optimizer, milestones=[25,50,75,100,125,150,175,200,225,230,240,250,260,270], gamma=0.8, verbose=False)
    criterion=torch.nn.MSELoss()

    # And the dataloader
    #seed them
    g = torch.Generator()
    g.manual_seed(0)

    train_loader = torch.utils.data.DataLoader(
        train_dataset,
        batch_size=opt.batch_size,
        pin_memory=False,
        num_workers=opt.num_workers,
        sampler=train_sampler,
        drop_last=True,
        worker_init_fn=seed_worker,
        generator=g
    )
    validation_loader = torch.utils.data.DataLoader(
        validation_dataset,
        batch_size=opt.batch_size,
        pin_memory=False,
        num_workers=opt.num_workers,
        sampler=validation_sampler,
        drop_last=True,
        worker_init_fn=seed_worker,
        generator=g
    )
    test_loader = torch.utils.data.DataLoader(
        test_dataset,
        batch_size=opt.batch_size,
        pin_memory=False,
        num_workers=opt.num_workers,
        sampler=test_sampler,
        drop_last=False,
        worker_init_fn=seed_worker,
        generator=g
    )

    losses_per_minibatch={  'q_loss_train':[],'q_risk_train':[],
                            'q_loss_valid':[],'q_risk_valid':[],
                            'nn_mse_train':[],'nrlmsise00_mse_train':[],'nn_mape_train':[],'nrlmsise00_mape_train':[],
                            'nn_mse_valid':[],'nrlmsise00_mse_valid':[],'nn_mape_valid':[],'nrlmsise00_mape_valid':[]}
    losses_total={  'q_loss_train':[],'q_risk_train':[],
                    'q_loss_valid':[],'q_risk_valid':[],
                    'nn_mse_train':[],'nrlmsise00_mse_train':[],'nn_mape_train':[],'nrlmsise00_mape_train':[],
                    'nn_mse_valid':[],'nrlmsise00_mse_valid':[],'nn_mape_valid':[],'nrlmsise00_mape_valid':[]}

    quantiles_tensor = torch.tensor(configuration["model"]["output_quantiles"]).to(device)

    best_loss_total_train = np.inf
    best_loss_train = np.inf
    best_loss_total_valid = np.inf
    best_loss_valid = np.inf

    best_q_loss_train = np.inf 
    best_q_loss_valid = np.inf 
    best_q_loss_total_train = np.inf 
    best_q_loss_total_valid = np.inf 
    criterion=torch.nn.MSELoss()
    for epoch in range(opt.epochs):
        #first training loop:
        q_loss_total=0.
        q_risk_total=0.
        loss_total_nn=0.
        loss_total_nrlmsise00=0.
        mape_total_nn=0.
        mape_total_nrlmsise00=0.
        #we set the model in training mode:
        tft_model.train()
        for batch_idx,el in enumerate(train_loader):
            #Just extracting the historical and future time series and making sure to concatenate in case there are multiple datasets
            historical_ts_numeric=[]
            if opt.omni_indices_path != 'None':
                historical_ts_numeric.append(el['omni_indices'][:,:-1,:])
            if opt.omni_magnetic_field_path != 'None':
                historical_ts_numeric.append(el['omni_magnetic_field'][:,:-1,:])
            if opt.omni_solar_wind_path != 'None':
                historical_ts_numeric.append(el['omni_solar_wind'][:,:-1,:])
            if opt.soho_path != 'None':
                historical_ts_numeric.append(el['soho'][:,:-1,:])
            if opt.nrlmsise00_path != 'None':
                historical_ts_numeric.append(el['msise'][:,:-1,:])
            if len(historical_ts_numeric)>1:
                historical_ts_numeric=torch.cat(historical_ts_numeric,dim=2)
            else:
                historical_ts_numeric=historical_ts_numeric[0]

            future_ts_numeric=el['msise'][:,-1,:].unsqueeze(1)
            historical_ts_numeric=historical_ts_numeric.to(device)
            future_ts_numeric=future_ts_numeric.to(device)

            minibatch = {
                    'static_feats_numeric': el['instantaneous_features'].to(device),
                    'historical_ts_numeric': historical_ts_numeric,
                    'future_ts_numeric':  future_ts_numeric,#batch size x future steps x num features
                    'target': el['target'].to(device)
                    }
            #let's store the normalized and unnormalized target density:
            target=el['target'].to(device)
            rho_target=el['ground_truth'].detach().cpu().numpy()
            batch_out=tft_model(minibatch)
            #now the quantiles:
            predicted_quantiles = batch_out['predicted_quantiles']#it's of shape batch_size x future_steps x num_quantiles
            target_nn_median=predicted_quantiles[:, :, 0].squeeze()
            q_loss, q_risk, _ = tft_loss.get_quantiles_loss_and_q_risk(outputs=predicted_quantiles,
                                                                        targets=target,
                                                                        desired_quantiles=quantiles_tensor)
            #now the normalized and unnormalized NN-predicted density:
            #if opt.train_type=='log_exp_residual':
            #    out_nn=torch.tanh(tft_model(minibatch).squeeze())
            #    target_nn=karman_dataset.scale_density(el['exponential_atmosphere'].to(device))+out_nn
            #else:
            #    target_nn=tft_model(minibatch).squeeze()
            rho_nn=karman_dataset.unscale_density(target_nn_median.detach().cpu()).numpy()
            #finally the NRLMSISE-00 ones:
            rho_nrlmsise00=el['nrlmsise00'].detach().cpu().numpy()
            target_nrlmsise00=karman_dataset.scale_density(el['nrlmsise00'].to(device))
            #now the loss computation:
            loss_nn = criterion(target_nn_median, target)
            loss_nrlmsise00 = mse(target_nrlmsise00.detach().cpu().numpy(), target.detach().cpu().numpy())

            # Zeroes the gradient 
            optimizer.zero_grad()

            # Backward pass: compute gradient of the loss with respect to model parameters
            #q_loss.backward()
            loss_nn.backward()

            # Calling the step function on an Optimizer makes an update to its parameters
            optimizer.step()

            #We compute the logged quantities
            #log to wandb:
            if opt.wandb_inactive==False:
                wandb.log({ 'q_loss_train':q_loss.item(),
                            'nn_mse_train':loss_nn.item(),
                            'nrlmsise00_mse_train':loss_nrlmsise00,
                            'nn_mape_train':mean_absolute_percentage_error(rho_nn, rho_target),
                            'nrlmsise00_mape_train':mean_absolute_percentage_error(rho_nrlmsise00, rho_target)})
            
            losses_per_minibatch['q_loss_train'].append(q_loss.item())
            losses_per_minibatch['q_risk_train'].append(q_risk.detach().cpu().numpy())
            losses_per_minibatch['nn_mse_train'].append(loss_nn.item())
            losses_per_minibatch['nrlmsise00_mse_train'].append(loss_nrlmsise00)
            losses_per_minibatch['nn_mape_train'].append(mean_absolute_percentage_error(rho_nn, rho_target))
            losses_per_minibatch['nrlmsise00_mape_train'].append(mean_absolute_percentage_error(rho_nrlmsise00, rho_target))
            #now let's also accumulate them for the overall loss computation in each epoch:
            q_loss_total+=losses_per_minibatch['q_loss_train'][-1]
            q_risk_total+=losses_per_minibatch['q_risk_train'][-1]
            loss_total_nn+=losses_per_minibatch['nn_mse_train'][-1]
            loss_total_nrlmsise00+=losses_per_minibatch['nrlmsise00_mse_train'][-1]
            mape_total_nn+=losses_per_minibatch['nn_mape_train'][-1]
            mape_total_nrlmsise00+=losses_per_minibatch['nrlmsise00_mape_train'][-1]
            
            #Save the best model (this is wrong and should be done on the dataset):
            if loss_nn.item()<best_loss_train:    
                best_loss_train=loss_nn.item()
            #Save the best model (this is wrong and should be done on the dataset):
            if q_loss.item()<best_q_loss_train:    
                best_q_loss_train=q_loss.item()

            #Print every 10 minibatches:
            #if batch_idx%10:    
            #    print(f'minibatch: {batch_idx}/{len(train_loader)}, best minibatch loss till now: {best_loss_train:.4e}, NN MSE: {losses_per_minibatch['nn_mse_train'][-1]:.10f}, nrlmsise00 MSE: {losses_per_minibatch['nrlmsise00_mse_train'][-1]:.10f}, NN MAPE: {losses_per_minibatch['nn_mape_train'][-1]:.3f}, nrlmsise00 MAPE: {losses_per_minibatch['nrlmsise00_mape_train'][-1]:.3f}', end='\r')
        #log to wandb:
        if opt.wandb_inactive==False:
                
            wandb.log({     'q_loss_train_total':q_loss_total/len(train_loader),
                            'nn_mse_train_total':loss_total_nn/len(train_loader),
                            'nrlmsise00_mse_train_total':loss_total_nrlmsise00/len(train_loader),
                            'nn_mape_train_total':mape_total_nn/len(train_loader),
                            'nrlmsise00_mape_train_total':mape_total_nrlmsise00/len(train_loader)})
        # over the whole dataset, we take the average of the minibatch losses:
        losses_total['q_loss_train'].append(q_loss_total/len(train_loader))
        losses_total['q_risk_train'].append(q_risk_total/len(train_loader))
        losses_total['nn_mse_train'].append(loss_total_nn/len(train_loader))
        losses_total['nrlmsise00_mse_train'].append(loss_total_nrlmsise00/len(train_loader))
        losses_total['nn_mape_train'].append(mape_total_nn/len(train_loader))
        losses_total['nrlmsise00_mape_train'].append(mape_total_nrlmsise00/len(train_loader))

        #update best total loss:
        if losses_total['nn_mse_train'][-1] < best_loss_total_train:
            best_loss_total_train=losses_total['nn_mse_train'][-1]
        #Print at the end of the epoch
        #curr_lr = scheduler.optimizer.param_groups[0]['lr']
        print(" "*300, end="\r")    
        print("\nTraining")
        print(f'Epoch {epoch + 1}/{opt.epochs}, NN MSE (total): {losses_total['nn_mse_train'][-1]:.7f}, nrlmsise00 MSE (total): {losses_total['nrlmsise00_mse_train'][-1]:.7f}, NN MAPE (total): {losses_total['nn_mape_train'][-1]:.3f}, nrlmsise00 MAPE (total): {losses_total['nrlmsise00_mape_train'][-1]:.3f}')
        # Perform a step in LR scheduler to update LR
        #scheduler.step()
        
        #Validation loop:
        q_loss_total=0.
        q_risk_total=0.
        loss_total_nn=0.
        loss_total_nrlmsise00=0.
        mape_total_nn=0.
        mape_total_nrlmsise00=0.
        #let's switch the model to evaluation mode:
        tft_model.eval()
        with torch.no_grad():
            for batch_idx,el in enumerate(validation_loader):
                historical_ts_numeric=[]
                if opt.omni_indices_path != 'None':
                    historical_ts_numeric.append(el['omni_indices'][:,:-1,:])
                if opt.omni_magnetic_field_path != 'None':
                    historical_ts_numeric.append(el['omni_magnetic_field'][:,:-1,:])
                if opt.omni_solar_wind_path != 'None':
                    historical_ts_numeric.append(el['omni_solar_wind'][:,:-1,:])
                if opt.soho_path != 'None':
                    historical_ts_numeric.append(el['soho'][:,:-1,:])
                if opt.nrlmsise00_path != 'None':
                    historical_ts_numeric.append(el['msise'][:,:-1,:])

                if len(historical_ts_numeric)>1:
                    historical_ts_numeric=torch.cat(historical_ts_numeric,dim=2)
                else:
                    historical_ts_numeric=historical_ts_numeric[0]
                future_ts_numeric=el['msise'][:,-1,:].unsqueeze(1)
                historical_ts_numeric=historical_ts_numeric.to(device)
                future_ts_numeric=future_ts_numeric.to(device)

                minibatch = {
                        'static_feats_numeric': el['instantaneous_features'].to(device),
                        'historical_ts_numeric': historical_ts_numeric,
                        'future_ts_numeric':  future_ts_numeric,#batch size x future steps x num features
                        'target': el['target'].to(device)
                        }
                #let's store the normalized and unnormalized target density:
                target=el['target'].to(device)
                rho_target=el['ground_truth'].detach().cpu().numpy()
                batch_out=tft_model(minibatch)
                #now the quantiles:
                predicted_quantiles = batch_out['predicted_quantiles']
                target_nn_median=predicted_quantiles[:, :, 0].squeeze()
                q_loss, q_risk, _ = tft_loss.get_quantiles_loss_and_q_risk(outputs=predicted_quantiles,
                                                                            targets=target,
                                                                            desired_quantiles=quantiles_tensor)
                #now the normalized and unnormalized NN-predicted density:
                #if opt.valid_type=='log_exp_residual':
                #    out_nn=torch.tanh(tft_model(minibatch).squeeze())
                #    target_nn=karman_dataset.scale_density(el['exponential_atmosphere'].to(device))+out_nn
                #else:
                #    target_nn=tft_model(minibatch).squeeze()
                rho_nn=karman_dataset.unscale_density(target_nn_median.detach().cpu()).numpy()
                #finally the NRLMSISE-00 ones:
                rho_nrlmsise00=el['nrlmsise00'].detach().cpu().numpy()
                target_nrlmsise00=karman_dataset.scale_density(el['nrlmsise00'].to(device))
                #now the loss computation:
                loss_nn = criterion(target_nn_median, target)
                loss_nrlmsise00 = mse(target_nrlmsise00.detach().cpu().numpy(), target.detach().cpu().numpy())
                #We compute the logged quantities
                #log to wandb:
                if opt.wandb_inactive==False:
                    wandb.log({'q_loss_valid':q_loss.item(),
                                'nn_mse_valid':loss_nn.item(),'nrlmsise00_mse_valid':loss_nrlmsise00,
                                'nn_mape_valid':mean_absolute_percentage_error(rho_nn, rho_target),
                                'nrlmsise00_mape_valid':mean_absolute_percentage_error(rho_nrlmsise00, rho_target)})
                
                losses_per_minibatch['q_loss_valid'].append(q_loss.item())
                losses_per_minibatch['q_risk_valid'].append(q_risk.detach().cpu().numpy())
                losses_per_minibatch['nn_mse_valid'].append(loss_nn.item())
                losses_per_minibatch['nrlmsise00_mse_valid'].append(loss_nrlmsise00)
                losses_per_minibatch['nn_mape_valid'].append(mean_absolute_percentage_error(rho_nn, rho_target))
                losses_per_minibatch['nrlmsise00_mape_valid'].append(mean_absolute_percentage_error(rho_nrlmsise00, rho_target))
                #now let's also accumulate them for the overall loss computation in each epoch:
                q_loss_total+=losses_per_minibatch['q_loss_valid'][-1]
                q_risk_total+=losses_per_minibatch['q_risk_valid'][-1]
                loss_total_nn+=losses_per_minibatch['nn_mse_valid'][-1]
                loss_total_nrlmsise00+=losses_per_minibatch['nrlmsise00_mse_valid'][-1]
                mape_total_nn+=losses_per_minibatch['nn_mape_valid'][-1]
                mape_total_nrlmsise00+=losses_per_minibatch['nrlmsise00_mape_valid'][-1]
                
                #Save the best model (this is wrong and should be done on the dataset):
                if loss_nn.item()<best_loss_valid:    
                    best_loss_valid=loss_nn.item()
                #Save the best model (this is wrong and should be done on the dataset):
                if q_loss.item()<best_q_loss_valid:    
                    best_q_loss_valid=q_loss.item()

                #Print every 10 minibatches:
                #if batch_idx%10:    
                #    print(f'minibatch: {batch_idx}/{len(validation_loader)}, best minibatch loss till now: {best_loss_valid:.4e}, NN MSE: {losses_per_minibatch['nn_mse_valid'][-1]:.10f}, nrlmsise00 MSE: {losses_per_minibatch['nrlmsise00_mse_valid'][-1]:.10f}, NN MAPE: {losses_per_minibatch['nn_mape_valid'][-1]:.3f}, nrlmsise00 MAPE: {losses_per_minibatch['nrlmsise00_mape_valid'][-1]:.3f}', end='\r')
            #log to wandb:
            if opt.wandb_inactive==False:
                    
                wandb.log({     'q_loss_valid_total':q_loss_total/len(validation_loader),
                                'nn_mse_valid_total':loss_total_nn/len(validation_loader),
                                'nrlmsise00_mse_valid_total':loss_total_nrlmsise00/len(validation_loader),
                                'nn_mape_valid_total':mape_total_nn/len(validation_loader),
                                'nrlmsise00_mape_valid_total':mape_total_nrlmsise00/len(validation_loader)})
            # over the whole dataset, we take the average of the minibatch losses:
            losses_total['q_loss_valid'].append(q_loss_total/len(validation_loader))
            losses_total['q_risk_valid'].append(q_risk_total/len(validation_loader))
            losses_total['nn_mse_valid'].append(loss_total_nn/len(validation_loader))
            losses_total['nrlmsise00_mse_valid'].append(loss_total_nrlmsise00/len(validation_loader))
            losses_total['nn_mape_valid'].append(mape_total_nn/len(validation_loader))
            losses_total['nrlmsise00_mape_valid'].append(mape_total_nrlmsise00/len(validation_loader))

        print("\nValidation")
        print(f'Epoch {epoch + 1}/{opt.epochs}, NN MSE (total): {losses_total['nn_mse_valid'][-1]:.7f}, nrlmsise00 MSE (total): {losses_total['nrlmsise00_mse_valid'][-1]:.7f}, NN MAPE (total): {losses_total['nn_mape_valid'][-1]:.3f}, nrlmsise00 MAPE (total): {losses_total['nrlmsise00_mape_valid'][-1]:.3f}')
        #updating torch best model:
        if losses_total['nn_mse_valid'][-1] < best_loss_total_valid:
            #log to wandb:
            #wandb.log({'best_nn_mse_valid':losses_total['nn_mse_valid'][-1]})
            #create directory if it does not exist:
            import os
            if not os.path.exists('../models'):
                os.makedirs('../models')
            torch.save(tft_model.state_dict(), f'../models/tft_model_tft_{opt.run_name}_valid_mape_{losses_total['nn_mape_valid'][-1]:.3f}_params_{num_params}.torch')
            best_loss_total_valid=losses_total['nn_mse_valid'][-1]

if __name__ == "__main__":
    time_start = time.time()
    train()
    print('\nTotal duration: {}'.format(time.time() - time_start))
    sys.exit(0)

