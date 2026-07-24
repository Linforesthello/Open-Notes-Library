%% 步骤 1: 导入数据并设置采样时间 (Ts)

% ----------------------------------------------------
% 文件名设置
filename = 'test_2.csv';
Ts = 0.01; % 采样时间：10 毫秒 = 0.01 秒
% ----------------------------------------------------

try
    data_matrix = readmatrix(filename);
catch ME
    error('无法读取文件 %s。请确认文件存在且路径正确。\n错误信息: %s', filename, ME.message);
end

% 提取关键列数据 (根据您的描述)
% 第三列：实际转速 (输出 y)
Actual_Speed =  data_matrix(:, 3);  
% 第四列：目标速度 (输入 u)
Target_Speed = data_matrix(:, 4);  

fprintf('数据导入成功。采样时间 Ts 设定为 %.3f 秒 (10ms)。\n', Ts);

% ！！！ 关键：极性处理 ！！！
% 如果模型增益为负，且您认为应为正，请在下一行取消注释：
% Actual_Speed = -Actual_Speed;
% fprintf('!!! 注意: 实际转速数据已取反，以解决模型增益为负的问题。!!!\n');

% 数据长度已匹配
Input_u = Target_Speed; 
Output_y = Actual_Speed; 

%% 步骤 2: 数据预处理和创建 iddata 对象

% 1. 去除数据的平均值 (去趋势 Detrend)
Input_u_detrend = Input_u - mean(Input_u);
Output_y_detrend = Output_y - mean(Output_y);

% 2. 创建完整的 iddata 对象
data = iddata(Output_y_detrend, Input_u_detrend, Ts);

% 3. 确保 Ts 被正确设置为离散时间
if data.Ts == 0
    data.Ts = Ts; 
    fprintf('iddata对象的Ts已被强制设置为 %.3f s。\n', data.Ts);
end

% 4. 可视化原始数据 (可选，确认数据极性)
figure('Name', '数据可视化 - 完整数据集');
plot(data);
title('输入 (目标速度) vs. 输出 (实际转速) 数据 (完整)');

%% 步骤 3: 数据截断和分割 (恢复和修正逻辑)

% 1. 定义截断范围
Start_Index = 25000; % 截断开始位置
End_Index   = 50000; % 截断结束位置
 
N_total = size(data, 1); 
End_Index = min(End_Index, N_total);

% 2. 截取需要用于辨识的原始数据段
data_segment = data(Start_Index : End_Index, :);

% 3. 将截取后的数据分割为辨识和验证集 (80% / 20%)
N_seg = size(data_segment, 1);
N_est = round(0.8 * N_seg); 

data_est = data_segment(1:N_est, :);        % 用于辨识
data_val = data_segment(N_est+1:end, :);    % 用于验证

fprintf('\n数据已截断并分割: 总点数 %d。辨识集 %d，验证集 %d。\n', N_seg, size(data_est, 1), size(data_val, 1));

% 4. 可视化截断后的辨识数据集 (确认截断效果)
figure('Name', '辨识数据集可视化 (已截断)');
plot(data_est);
title(sprintf('用于辨识的数据, 从点 %d 开始', Start_Index));

%% 步骤 4: 辨识黑箱模型 (状态空间 SS - 推荐)

% 尝试 2 阶状态空间模型 (通常足以描述电机速度)
Model_Order = 2; 

fprintf('\n开始辨识离散时间状态空间模型 (阶次=%d, Ts=%.3fs)...\n', Model_Order, Ts);

% ！！！ 使用 data_est 进行估计 ！！！
sys_ss = ssest(data_est, Model_Order, 'Ts', Ts); 

% 将结果命名为 sys_tf 以保持后续代码一致，方便使用 pidTuner
sys_tf = sys_ss;

% 显示模型结果
disp('--------------------------------------------------');
disp('辨识的离散时间状态空间模型 sys_ss (即 sys_tf):');
disp(sys_ss); 
disp('--------------------------------------------------');


%% 步骤 5: 模型验证

% 1. 拟合度比较 (使用 data_val 进行验证)
figure('Name', '时域拟合比较');
compare(data_val, sys_tf);

% 2. 获取拟合度 (修正字段名错误)
try
    fit_percent = sys_tf.Report.Fit.Value(1); 
    title(sprintf('模型拟合度 (Fit Percentage: %.2f%%) - 验证集', fit_percent));
    fprintf('模型拟合优度 (验证集): %.2f%%\n', fit_percent);
catch
    warning('无法自动获取拟合度。请手动检查 sys_tf.Report.Fit 结构体。');
    fit_percent = 0; 
end

% 3. 残差分析
figure('Name', '残差分析');
resid(data_est, sys_tf); 

if fit_percent < 70
    fprintf('\n!!! 警告: 模型拟合度低于 70%%。请尝试调整阶次 (如 Model_Order=3) 或检查数据激励是否充足。!!!\n');
end

% --------------------------------------------------
% 最终用途：导出模型用于 PID 调优
% --------------------------------------------------
fprintf('\n模型辨识完成。您现在可以使用 sys_tf 进行离线 PID 调优：\n');
fprintf('>> pidTuner(sys_tf)\n');